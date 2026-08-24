# Reglas de Negocio — Precios y SKU

## Reglas de precio de productos

Toda operación de dinero usa `Decimal`; nunca `float`. Precios almacenados en `NUMERIC(14,2)`.

| Regla | Descripción |
|---|---|
| `FIXED_PEN` | Precio fijo en soles (PEN). Se muestra tal cual. |
| `FIXED_USD` | Precio fijo en dólares (USD). Se muestra tal cual (los dólares se convierten a PEN en el precio vigente de tienda). |
| `USD_CONVERTED` | El precio se convierte de USD a PEN con el tipo de cambio vigente al consultar. |
| `COST_USD_MARGIN` | Costo en USD + margen configurado (reservado; se completa en fases de ventas/márgenes). |
| `MANUAL` | Precio fijado manualmente sin cálculo automático. |

### Precio vigente (`get_current_price`)

El orden efectivo implementado es:

1. Si el producto tiene una `ProductOffer` activa con `start_at <= NOW() <= end_at` → se usa el `offer_price`.
2. Si no, se usa `sale_price`.
3. Se muestra en PEN (soles) si:
   - `price_rule == "USD_CONVERTED"`, o
   - `currency == "USD"`.
   La conversión usa la tasa USD→PEN vigente y redondea a 2 decimales (`Decimal("0.01")`).

Ofertas: una oferta es válida solo si está `active=True` y la fecha actual está dentro de `[start_at, end_at]`. Crear oferta exige `offer_price < normal_price` y `end_at > start_at`.

## Generador de SKU

Formato: `{PREFIJO}-{secuencia:05d}` → `LAP-00001`.

- Tabla auxiliar `sku_sequences` (`prefix` VARCHAR PK, `last_value` INT).
- El SKU se genera **dentro de la misma transacción** que crea el producto:
  - `SELECT last_value ... WHERE prefix = :prefix FOR UPDATE`
  - Incremento en 1 y commit con el producto.
- Esto garantiza unicidad bajo concurrencia (test: 100 creates simultáneos → 100 SKUs únicos).
- El SKU nunca se modifica después de creado.

### Prefijos por categoría

Los prefijos son configurables por slug de categoría en `SKU_PREFIX_BY_CATEGORY_SLUG` (settings). Si la categoría no tiene prefijo mapeado, se usa `SKU_DEFAULT_PREFIX` (`PRD`).

Prefijos de semilla (cargados por `seed_sku_prefixes`):

| Prefijo | Uso típico |
|---|---|
| `LAP` | Laptops |
| `IMP` | Impresoras |
| `CAM` | Cámaras |
| `ACC` | Accesorios |
| `ELE` | Electrodomésticos |
| `SRV` | Servicios |
| `SBL` | Sublimación |
| `MON` | Monitores |
| `CEL` | Celulares |
| `TAB` | Tablets |
| `RED` | Redes |
| `ALM` | Alarmas / seguridad |

## Modelo de inventario basado en movimientos (#F03-01 — #F03-05)

El stock **nunca es un campo** (`products.stock`). Se calcula como suma algebraica de `inventory_movements.quantity`.

| Tipo `movement_type` | Signo | Cuándo | `reference_type` |
|---|---|---|---|
| `PURCHASE` | + | Recepción de compra (`POST /purchases/{id}/receive`) | `purchase` |
| `SALE` | - | Venta confirmada | `sale` |
| `RESERVATION` | - | Reserva temporal (se resta de `available`) | `sale` |
| `RELEASE_RESERVATION` | + | Liberación de reserva | `sale` |
| `PARTIAL_PAYMENT_HOLD` | - | Apartado / pago parcial | `sale` |
| `CREDIT_DELIVERY` / `SALE_COMPLETED` | -/+ | Entrega a crédito y liquidación | `sale` |
| `RETURN` / `REPAIR_RETURN` | + | Devolución / retorno de reparación | `return`/`repair` |
| `ADJUSTMENT_IN` / `ADJUSTMENT_OUT` | +/- | Conteo físico (requiere `authorization_id` → `AuditLog`) | `adjustment` |
| `REPAIR_USAGE` / `DAMAGED` / `TRANSFER` | - | Consumo en reparación, dañado, traslado | `repair` |

### Cálculo de stock (`get_stock_summary` — #F03-02)

Una sola query agregada (sin `float`, todo `Decimal`/`NUMERIC`):

```
physical       = SUM(quantity WHERE type IN PHYSICAL_IN ∪ PHYSICAL_OUT)
reserved       = -SUM(quantity WHERE type IN {RESERVATION,RELEASE_RESERVATION})
partially_paid = -SUM(quantity WHERE type = PARTIAL_PAYMENT_HOLD)
on_credit      = -SUM(quantity WHERE type IN {CREDIT_DELIVERY,SALE_COMPLETED})
available      = physical - reserved - partially_paid - on_credit
total_physical = physical
low_stock      = available <= product.stock_minimum
```

Vista `v_product_stock` precalcula por producto para listados masivos (`GET /inventory/stock?search=&low=`). `GET /inventory/kardex/{id}` devuelve saldo acumulado (`running_balance`) cronológico y export CSV (`/export`).

### Concurrencia (#F03-03)

Toda mutación hace `SELECT ... FOR UPDATE` sobre `products.id`. `quantity` es `NUMERIC(14,3)` y tests verifican `0.1 * 100 = 10.0` sin pérdida (`Decimal`). `InventoryMovement` es **inmutable**: repositorio solo `INSERT`, sin `update/delete`.

Ajustes: `POST /inventory/adjustments` solo `inventario.ajustar` (OWNER), con `reason` obligatorio, `AuditLog(ADJUST_INVENTORY)` → `authorization_id`.

## Flujo de caja (#F04-01/03)

`CashRegister` (caja del usuario) → `CashSession(OPEN)` + `CashMovement(OPENING)` idempotente (`ix_cash_sessions_user_open` WHERE `OPEN`). Balance = `SUM IN - SUM OUT`. Cierre: `POST /cash/sessions/{id}/close {counted_cash}` calcula `expected=get_balance()`, `difference=counted-expected`; si `0→CLOSED` inmediato, si `≠0→PENDING_CLOSURE` + `CashClosureRequest(PENDING)` → `POST /cash/closure-requests/{id}/approve|reject` solo OWNER (`AuditLog APPROVE_CASH_CLOSURE`).

Transferencia atómica `POST /cash/transfers {from,to,amount}`: `TRANSFER_OUT` + `TRANSFER_IN` + `CashTransfer` en 1 transacción (rollback si falla), verifica `get_balance(from) >= amount`.

## Venta al contado atómica (#F04-08)

`POST /sales {items, payments, cash_session_id, idempotency_key}` en 1 transacción:
`idempotency_key` check → `SELECT product FOR UPDATE` + `SerializedUnit FOR UPDATE` si serializado → `get_stock_summary` verifica `available>=qty` → `discount_authorization APPROVED` → `Sale(DRAFT)` + `SaleItem` + `SalePayment` + `CashMovement(SALE_INCOME)` + `InventoryMovement(SALE,-qty)` + `SerializedUnit.status=SOLD` → `status=PAID` → `AuditLog CREATE_SALE`. Si falla cualquier paso → `ROLLBACK`. Doble envío con mismo `idempotency_key` retorna venta existente.

Descuento: `POST /discounts/request` SALES → `PENDING` → `POST /discounts/{id}/approve` OWNER → `APPROVED`. `percentage<=1`, `fixed_amount>=0`, `AuditLog`.

Idempotencia: `DocumentSequence(prefix,year)` con `SELECT FOR UPDATE` genera `VTA-2026-00001`.

## Créditos, cuotas y mora (#F05)

### Validación pre-crédito (`validate_customer_for_credit` — #F05-04)

Se ejecuta antes de aprobar cualquier crédito, **en orden y deteniéndose en el primer bloqueo**:

| # | Regla | Bloqueo | Excepción |
|---|---|---|---|
| 1 | Morosidad activa (cuota `OVERDUE`) | `CUSTOMER_DELINQUENT` | `CreditAuthorization(OVERRIDE_DELINQUENCY)` OWNER |
| 2 | Límite: Σ saldos de cuotas vigentes + nuevo monto ≤ `customer.credit_limit` | `CREDIT_LIMIT_EXCEEDED` | `OVERRIDE_LIMIT` OWNER |
| 3 | Múltiples créditos en (`ACTIVE`,`OVERDUE`) | `MULTIPLE_CREDITS` | `MULTIPLE_CREDITS` OWNER |
| 4 | Inicial: si `initial_payment = 0` y cliente no frecuente → bloquea; si `initial < credit_min_initial_percent × total` → advertencia | `INITIAL_REQUIRED` | `WAIVE_INITIAL` OWNER |

Si pasa todo → `APPROVED`. El endpoint `POST /credits/validate` devuelve la lista de bloqueos/advertencias para que el frontend muestre qué autorización se necesita.

### Creación atómica del crédito (#F05-05)

`POST /credits` en 1 transacción: validación → `Sale(CREDIT, PARTIALLY_PAID)` + ítems con precio vigente (oferta > precio) → pago inicial como `SalePayment` + `CashMovement(CREDIT_PAYMENT)` si hay sesión abierta → `CreditAgreement(ACTIVE)` → N `CreditInstallment` → `InventoryMovement(RESERVATION,-qty)` + `SerializedUnit(RESERVED)` si aplica → `Reservation` → `AuditLog(CREATE_CREDIT)`. Cualquier fallo hace rollback total. TC se congela en el acuerdo al crear.

### Calendario de cuotas

- Base = `financed / n` (la última cuota absorbe el redondeo).
- Cuotas dentro de los `interest_free_months`: sin interés.
- Cuotas posteriores: `base + financed × interest_rate` (interés flat sobre el saldo financiado, nunca compuesto).

**Ejemplo** (#F05-23): crédito S/2500, inicial S/500 → financiado S/2000; 4 cuotas, 2 meses gracia, 3% después:
cuota1 = 500.00 (vence mes 1), cuota2 = 500.00 (mes 2), cuota3 = 560.00, cuota4 = 560.00.

### Pago de cuotas (#F05-06/#F05-07)

- `POST /installments/{id}/pay {amount, method, idempotency_key}`: `SELECT FOR UPDATE`; el pago cubre primero capital, luego mora. Parcial → `PARTIALLY_PAID` con `remaining_amount` actualizado; completo → `PAID`.
- Idempotencia por `idempotency_key` único: reenvío no duplica `CreditPayment` ni `CashMovement`.
- Última cuota pagada → `CreditAgreement(PAID)` + `Sale(COMPLETED)` + `InventoryMovement(SALE_COMPLETED)` + `SerializedUnit(SOLD)` + reservas a `CONVERTED_TO_SALE` + `AuditLog(CREDIT_COMPLETED)`.
- Pago adelantado `POST /credits/{id}/pay-multiple`: el monto se distribuye desde la cuota más antigua; un `CreditPayment` por cuota afectada; jamás altera pagos históricos.

### Mora mensual al 3% sin capitalizar (#F05-08/#F05-09)

- Tarea Celery `apply_daily_mora` (6 AM, America/Lima): solo actúa el día 1 del mes.
- Para cada cuota `PENDING/PARTIALLY_PAID` con `due_date < inicio del período`:
  - **Idempotencia**: `UNIQUE (installment_id, period)` en `credit_moras` + verificación previa → nunca doble mora.
  - `mora = remaining_amount × settings.MORA_RATE (0.03)` sobre **capital puro** → la mora del mes siguiente NO incluye moras anteriores (nunca capitaliza).
  - La cuota pasa a `OVERDUE` y su `mora_amount` acumula.
- Acuerdos: con cuotas vencidas → `OVERDUE`; superan `CREDIT_DEFAULTED_MIN_OVERDUE` → `DEFAULTED` + registro para notificar OWNER.
- Cálculo siempre con `Decimal`, redondeo a 2 decimales (`ROUND_HALF_UP`).

Ejemplo: capital S/100 vencido → mora mes 1 = 3.00 (deuda 103.00); mora mes 2 = 3.00 otra vez (**no** 3% sobre 103). Nunca se cobra mora sobre mora.

### Reprogramación (#F05-10) y entrega anticipada (#F05-11)

- `PUT /installments/{id}/restructure {new_due_date, reason}` solo OWNER; conserva `original_due_date` original, registra motivo en `AuditLog(RESTRUCTURE_CREDIT)`; si pasa de `OVERDUE` a fecha futura puede volver a `PENDING`.
- `POST /credits/{id}/deliver` solo OWNER (`creditos.aprobar`): libera reserva (`RELEASE_RESERVATION`), registra `CREDIT_DELIVERY`, serializados a `DELIVERED_ON_CREDIT` (no vuelven al stock vendible), reservas a `CONVERTED_TO_CREDIT`. Al cancelarse todo el crédito las unidades ya entregadas se liquidan vía `SALE_COMPLETED` cuando se paga la última cuota.

### Estados del crédito

```
PENDING_APPROVAL → APPROVED → ACTIVE ⇄ OVERDUE → PAID
                                    ↓
                               DEFAULTED
ACTIVE/APPROVED → CANCELLED ; ACTIVE → RESTRUCTURED
```

Inventario por etapa: creado → stock `reserved` (RESERVATION); entregado → `on_credit` (CREDIT_DELIVERY); pagado → `on_credit` liquidado (SALE_COMPLETED); nunca vuelve a `available` mientras exista el crédito.

---

*Referencia: [database.md](database.md), [REQUIREMENTS.md](REQUIREMENTS.md)*