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

---

*Referencia: [database.md](database.md), [REQUIREMENTS.md](REQUIREMENTS.md)*