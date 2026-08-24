# FASE 05 — Créditos, Cuotas y Mora

**Rama:** `feature/fase-05-creditos`
**Objetivo:** Sistema financiero de crédito completo con todas sus reglas de negocio, cuotas, mora mensual automática, reservas y entrega anticipada.
**Prerrequisito:** FASE 04 completada y mergeada a `develop`.
**Criterio de salida:** Crédito completo funciona con reglas de bloqueo. Mora calculada correctamente al 3% sin capitalizar. Todos los tests financieros de crédito pasan.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 30 | 30 | 100% |

> **Verificación 2026-08-24:** 112/112 tests API (`pytest`, incluye los 35 de `test_credits.py`), ruff y mypy limpios, seeds verificados (6 acuerdos: 3 ACTIVE, 1 OVERDUE con mora, 1 PAID con reserva convertida a venta, 1 DEFAULTED con mora en 2 períodos), `next build` OK con las vistas de créditos/cuotas/morosidad/portal cliente. Pendiente: PR → `develop`.

---

## Issues

### MODELOS

---

#### #F05-01 — Modelo CreditAgreement con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-04 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/credits/domain/models.py`:
  ```
  CreditAgreement:
    id (UUID, PK)
    code (VARCHAR, unique)              — CRD-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    sale_id (UUID, FK → Sale)
    status (ENUM):
      PENDING_APPROVAL/APPROVED/ACTIVE/PAID/OVERDUE/DEFAULTED/CANCELLED/RESTRUCTURED
    total_amount (NUMERIC(14,2))        — precio total del bien
    initial_payment (NUMERIC(14,2))     — inicial pagada
    financed_amount (NUMERIC(14,2))     — total - initial
    number_of_installments (INTEGER)
    installment_amount (NUMERIC(14,2))  — monto por cuota
    interest_rate (NUMERIC(5,4))        — tasa mensual (0.0300 = 3%)
    interest_free_months (INTEGER, default 0)
    currency (VARCHAR(3))
    exchange_rate (NUMERIC(10,4))       — TC congelado al crear
    exchange_rate_source (VARCHAR)
    exchange_rate_timestamp (TIMESTAMPTZ)
    first_due_date (DATE)
    authorized_by (UUID, FK → User)
    authorization_id (UUID, FK → CreditAuthorization)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

    CONSTRAINT: financed_amount = total_amount - initial_payment
    CONSTRAINT: installment_amount > 0
    CONSTRAINT: initial_payment >= 0
  ```
- [ ] Migración Alembic

---

#### #F05-02 — Modelo CreditInstallment y CreditPayment con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-01

**Tareas:**
- [ ] Crear modelos:
  ```
  CreditInstallment:
    id (UUID, PK)
    agreement_id (UUID, FK → CreditAgreement)
    number (INTEGER, not null)           — 1, 2, 3...
    amount (NUMERIC(14,2), not null)     — monto original
    due_date (DATE, not null)
    paid_amount (NUMERIC(14,2), default 0)
    remaining_amount (NUMERIC(14,2))     — amount - paid_amount
    mora_amount (NUMERIC(14,2), default 0)
    status (ENUM): PENDING/PARTIALLY_PAID/PAID/OVERDUE/RESTRUCTURED/CANCELLED
    original_due_date (DATE)             — antes de reprogramación
    restructured_at (TIMESTAMPTZ)
    restructured_by (UUID, FK → User)
    restructure_reason (TEXT)

  CreditPayment:
    id (UUID, PK)
    installment_id (UUID, FK → CreditInstallment)
    agreement_id (UUID, FK → CreditAgreement)
    amount (NUMERIC(14,2), not null)
    method (ENUM): CASH/YAPE/PLIN/CARD/BANK_TRANSFER/OTHER
    method_detail (VARCHAR)
    reference (VARCHAR)
    cash_session_id (UUID, FK → CashSession)
    idempotency_key (VARCHAR, unique)
    paid_at (TIMESTAMPTZ)
    registered_by (UUID, FK → User)

  CreditAuthorization:
    id (UUID, PK)
    customer_id (UUID, FK → Customer)
    type (ENUM):
      NEW_CREDIT/WAIVE_INITIAL/OVERRIDE_LIMIT/MULTIPLE_CREDITS/OVERRIDE_DELINQUENCY
    requested_by (UUID, FK → User)
    approved_by (UUID, FK → User)
    reason (TEXT, not null)
    status (ENUM): PENDING/APPROVED/REJECTED
    requested_at (TIMESTAMPTZ)
    reviewed_at (TIMESTAMPTZ)

  CreditMora:
    id (UUID, PK)
    installment_id (UUID, FK → CreditInstallment)
    agreement_id (UUID, FK → CreditAgreement)
    principal_vencido (NUMERIC(14,2))   — saldo base de cálculo
    rate (NUMERIC(5,4))                 — tasa aplicada (ej: 0.0300)
    mora_amount (NUMERIC(14,2))         — principal_vencido * rate
    period (VARCHAR)                    — YYYY-MM (ej: "2026-08")
    applied_at (TIMESTAMPTZ)
    generated_by (VARCHAR)              — "system" o username
    UNIQUE: (installment_id, period)    — idempotencia de mora
  ```
- [ ] Migración Alembic para todas las tablas de crédito
- [ ] Constraint UNIQUE en `(installment_id, period)` para CreditMora (evita doble mora)

---

#### #F05-03 — Modelo Reservation con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-01

**Tareas:**
- [ ] Crear modelo:
  ```
  Reservation:
    id (UUID, PK)
    product_id (UUID, FK → Product)
    serialized_unit_id (UUID, FK → SerializedUnit, nullable)
    customer_id (UUID, FK → Customer)
    sale_id (UUID, FK → Sale, nullable)
    credit_agreement_id (UUID, FK → CreditAgreement, nullable)
    status (ENUM): ACTIVE/EXPIRED/CANCELLED/CONVERTED_TO_SALE/CONVERTED_TO_CREDIT
    initial_amount (NUMERIC(14,2))
    expires_at (TIMESTAMPTZ)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] Una reserva activa genera InventoryMovement(RESERVATION)
- [ ] Al cancelar una reserva: InventoryMovement(RELEASE_RESERVATION)

---

### REGLAS DE NEGOCIO DE CRÉDITO

---

#### #F05-04 — Servicio de validación pre-crédito
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-01, #F05-02

**Descripción:**
Antes de aprobar cualquier crédito, el sistema debe ejecutar estas verificaciones en orden.

**Tareas:**
- [ ] Crear `CreditValidationService.validate_customer_for_credit(customer_id, amount, installments, user)`:
  ```
  Verificaciones en orden (detener en el primer bloqueo):

  1. MOROSIDAD ACTIVA:
     - Existe CreditInstallment con status=OVERDUE para este cliente?
     - SI → bloquear con CreditValidationError("CUSTOMER_DELINQUENT")
     - EXCEPCIÓN solo con CreditAuthorization(OVERRIDE_DELINQUENCY) de OWNER

  2. LÍMITE DE CRÉDITO:
     - créditos_activos_pendiente = SUM(remaining_amount de cuotas PENDING/PARTIALLY_PAID)
     - total_solicitado = amount
     - SI créditos_activos_pendiente + total_solicitado > customer.credit_limit:
       → alerta + bloquear hasta CreditAuthorization(OVERRIDE_LIMIT) de OWNER

  3. MÚLTIPLES CRÉDITOS ACTIVOS:
     - Tiene créditos con status IN (ACTIVE, OVERDUE)?
     - SI → bloquear hasta CreditAuthorization(MULTIPLE_CREDITS) de OWNER

  4. INICIAL:
     - ¿Se configuró initial_payment?
     - SI initial_payment == 0 Y NOT customer.is_frequent:
       → bloquear hasta CreditAuthorization(WAIVE_INITIAL) de OWNER
     - SI initial_payment < credit_min_initial_percent * total:
       → alerta (configurable en settings)

  5. SI PASA TODO → APPROVED para continuar
  ```
- [ ] Retornar lista de bloqueos para que el frontend muestre qué autorización se necesita

---

#### #F05-05 — Servicio de creación de crédito (operación atómica)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-04

**Tareas:**
- [ ] Implementar `create_credit_sale(sale_items, initial_payment, installments_config, authorizations, user)`:
  ```
  [TRANSACCIÓN ATÓMICA]:
  1. Ejecutar validate_customer_for_credit()
  2. Crear Sale(status=PARTIALLY_PAID, sale_type=CREDIT)
  3. Crear SaleItem × N
  4. Registrar pago inicial como SalePayment
  5. Crear CreditAgreement(status=ACTIVE)
  6. Generar CreditInstallment × N:
     - Calcular due_dates desde first_due_date
     - Aplicar interest_free_months: cuotas dentro del período = sin interés
     - Cuotas después del período = amount + (financed_amount * interest_rate)
  7. CashMovement(CREDIT_PAYMENT, initial_payment) en sesión activa
  8. InventoryMovement(RESERVATION, -qty) para cada producto
  9. Si es serializado: SerializedUnit.status = RESERVED
  10. Crear Reservation para cada producto
  11. AuditLog: CREATE_CREDIT con términos completos
  SI CUALQUIER PARTE FALLA: ROLLBACK
  ```
- [ ] Endpoints:
  - `POST /api/v1/credits` — crear crédito
  - `GET /api/v1/credits` — lista (OWNER + SALES con filtros)
  - `GET /api/v1/credits/{id}` — detalle completo con cuotas
  - `GET /api/v1/credits/customer/{customer_id}` — créditos de un cliente

---

#### #F05-06 — Pago de cuotas (contado y parcial)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] Implementar `pay_installment(installment_id, amount, method, reference, idempotency_key, session_id, user)`:
  ```
  [TRANSACCIÓN ATÓMICA]:
  1. Verificar idempotency_key
  2. SELECT installment FOR UPDATE
  3. paid_this_time = amount
  4. nueva_paid_amount = installment.paid_amount + paid_this_time
  5. SI nueva_paid_amount >= installment.amount + installment.mora_amount:
       installment.status = PAID
       installment.remaining_amount = 0
  6. SI nueva_paid_amount < total_adeudado:
       installment.status = PARTIALLY_PAID
       installment.paid_amount = nueva_paid_amount
       installment.remaining_amount = total_adeudado - nueva_paid_amount
  7. Crear CreditPayment
  8. CashMovement(CREDIT_PAYMENT, IN) en sesión activa
  9. Verificar si TODAS las cuotas del acuerdo están PAID:
       SI → CreditAgreement.status = PAID
           → Sale.status = COMPLETED
           → InventoryMovement(SALE_COMPLETED)
           → SerializedUnit.status = SOLD (si aplica)
           → AuditLog: CREDIT_COMPLETED
  10. AuditLog: CREDIT_PAYMENT
  ```
- [ ] Endpoints:
  - `POST /api/v1/installments/{id}/pay` — pagar cuota
  - `GET /api/v1/installments/{id}` — detalle de cuota
  - `GET /api/v1/credits/{id}/installments` — todas las cuotas de un crédito

---

#### #F05-07 — Pago adelantado de múltiples cuotas
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-06

**Tareas:**
- [ ] Implementar `pay_multiple_installments(agreement_id, installment_ids, amount, method, idempotency_key, user)`:
  - El amount se distribuye entre las cuotas seleccionadas en orden (primero la más antigua)
  - Registrar exactamente qué cuotas fueron afectadas
  - Un CreditPayment por cuota pagada (trazabilidad completa)
  - Nunca alterar el historial de pagos anteriores
- [ ] Endpoint: `POST /api/v1/credits/{id}/pay-multiple`

---

### MORA

---

#### #F05-08 — Lógica de mora mensual
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-02

**Tareas:**
- [ ] Crear `MoraService.apply_mora_for_period(period: str)`:
  ```
  1. Buscar todas las CreditInstallment con:
     - status IN (PENDING, PARTIALLY_PAID)
     - due_date < primer día del período actual
  2. Para cada cuota vencida:
     a. Verificar que NO existe CreditMora con (installment_id, period)  ← IDEMPOTENCIA
     b. principal_vencido = installment.remaining_amount
     c. rate = settings.mora_rate (default 0.0300)
     d. mora_amount = principal_vencido * rate
     e. Crear CreditMora (period, rate, mora_amount)
     f. installment.mora_amount += mora_amount
     g. installment.status = OVERDUE (si no estaba ya)
  3. Para cada CreditAgreement con cuotas OVERDUE:
     - Verificar umbral de morosidad (configurable)
     - Si supera: CreditAgreement.status = DEFAULTED
     - Crear Notification para OWNER
  ```
- [ ] **NUNCA capitalizar mora sobre mora** — se calcula siempre sobre `remaining_amount` original
- [ ] La tasa NO incluye mora acumulada en el cálculo del mes siguiente

---

#### #F05-09 — Tarea Celery: mora diaria automática
- **Tipo:** `[TASK]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-08

**Tareas:**
- [ ] Crear `apps/worker/tasks/mora.py`:
  - Tarea `apply_daily_mora()` — verifica si hoy es el primer día del mes
  - Si sí: llama `MoraService.apply_mora_for_period(current_period)`
  - La tarea es idempotente: si se ejecuta dos veces en el mismo día, no duplica mora
- [ ] Configurar en Beat: diariamente a las 6 AM
- [ ] Si la tarea falla: retry automático + notificación al OWNER
- [ ] Loguear: cuántas cuotas procesadas, cuánta mora total generada

---

#### #F05-10 — Reprogramación de cuotas (solo OWNER)
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] Implementar `restructure_installment(installment_id, new_due_date, reason, owner_user)`:
  - Solo OWNER puede reprogramar
  - Guarda `original_due_date` (no se sobrescribe en reprogramaciones posteriores)
  - Registra: old_due_date, new_due_date, reason, authorized_by, timestamp
  - Si la cuota pasa de OVERDUE a fecha futura: puede cambiar a PENDING
  - AuditLog: RESTRUCTURE_CREDIT
- [ ] Endpoint: `PUT /api/v1/installments/{id}/restructure`

---

### ENTREGA ANTES DE PAGO TOTAL

---

#### #F05-11 — Flujo de entrega anticipada (DELIVERED_ON_CREDIT)
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] Implementar `deliver_on_credit(agreement_id, user)`:
  ```
  [TRANSACCIÓN ATÓMICA]:
  - Verificar que CreditAgreement.status IN (ACTIVE, APPROVED)
  - Para cada producto de la venta:
    - InventoryMovement(CREDIT_DELIVERY)
    - SerializedUnit.status = DELIVERED_ON_CREDIT
    - Reservation.status = CONVERTED_TO_CREDIT
  - AuditLog: DELIVER_ON_CREDIT
  ```
- [ ] Al completar todas las cuotas (en `pay_installment`):
  ```
  - InventoryMovement(SALE_COMPLETED)
  - SerializedUnit.status = SOLD
  - CreditAgreement.status = PAID
  - Sale.status = COMPLETED
  ```
- [ ] Endpoint: `POST /api/v1/credits/{id}/deliver`

---

### FRONTEND

---

#### #F05-12 — Vista de créditos (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] `apps/web/app/admin/creditos/page.tsx` — lista de créditos con filtros
- [ ] Filtros: estado, cliente, vendedor, fecha, morosidad
- [ ] Indicadores visuales:
  - 🔴 DEFAULTED (en mora grave)
  - 🟠 OVERDUE (cuotas vencidas)
  - 🟢 ACTIVE (al día)
  - ⚫ PAID (completado)
- [ ] `apps/web/app/admin/creditos/nuevo/page.tsx` — formulario de crédito:
  - Selección de cliente
  - Verificación automática en tiempo real (morosidad, límite, etc.)
  - Si hay bloqueos: mostrar qué autorizaciones se necesitan
  - Configuración de cuotas: cantidad, fecha inicio, meses de gracia, tasa
  - Preview de calendario de pagos antes de confirmar
- [ ] `apps/web/app/admin/creditos/[id]/page.tsx` — detalle con checklist de cuotas

---

#### #F05-13 — Vista de cuotas (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-06

**Tareas:**
- [ ] `apps/web/app/admin/cuotas/page.tsx` — todas las cuotas del sistema
- [ ] Filtros: estado (PENDING, OVERDUE, PAID), cliente, fecha de vencimiento
- [ ] Vista del cliente: checklist visual con estados:
  - ✅ Pagada completamente
  - ◐ Pagada parcialmente (con monto pendiente)
  - ☐ Pendiente
  - ⚠️ Vencida
  - ⚡ Con mora
- [ ] Modal de pago de cuota:
  - Monto a pagar (puede ser parcial)
  - Método de pago
  - Si hay mora: mostrar desglose (capital + mora)
  - Confirmación con resumen

---

#### #F05-14 — Vista de morosidad (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-08

**Tareas:**
- [ ] `apps/web/app/admin/morosidad/page.tsx`
- [ ] Tabla de clientes con cuotas vencidas:
  - Nombre del cliente, créditos activos, cuotas vencidas, monto total en mora, días de atraso
- [ ] Resumen: total de mora en el sistema, clientes afectados
- [ ] Acción: reprogramar cuota, registrar pago, ver detalle del cliente
- [ ] Solo visible para OWNER

---

#### #F05-15 — Portal del cliente: mis cuotas
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] `apps/web/app/customer/cuotas/page.tsx`
- [ ] Lista de créditos activos con sus cuotas
- [ ] Checklist visual de cuotas (✅ ◐ ☐ ⚠️)
- [ ] Monto total pendiente destacado
- [ ] Próxima cuota a vencer con fecha y monto
- [ ] Historial de pagos realizados

---

### SEEDS

---

#### #F05-16 — Seeds de créditos ficticios
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] 3 créditos activos (ACTIVE) con cuotas PENDING
- [ ] 1 crédito con cuota vencida (OVERDUE) con mora calculada
- [ ] 1 crédito completamente pagado (PAID)
- [ ] 1 crédito DEFAULTED (cliente moroso)
- [ ] Todos con datos completamente ficticios

---

### TESTS FINANCIEROS CRÍTICOS

---

#### #F05-17 — Tests de validación pre-crédito
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-04

**Tareas:**
- [ ] `test_delinquent_customer_blocked` — cliente moroso no puede tomar crédito → error
- [ ] `test_delinquent_override_requires_owner` — solo OWNER puede sobrescribir bloqueo
- [ ] `test_credit_limit_enforced` — superar límite bloquea sin autorización
- [ ] `test_multiple_credits_require_authorization` — segundo crédito requiere OWNER
- [ ] `test_initial_required_for_non_frequent` — sin inicial y cliente no frecuente → error
- [ ] `test_frequent_customer_can_waive_initial_with_owner` — cliente frecuente + OWNER → OK

---

#### #F05-18 — Tests de creación de crédito (transacción atómica)
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-05

**Tareas:**
- [ ] `test_credit_creates_correct_installments` — N cuotas generadas correctamente
- [ ] `test_credit_interest_free_months_applied` — cuotas dentro de período sin interés
- [ ] `test_credit_interest_applied_after_free_months` — cuotas fuera de período con interés
- [ ] `test_credit_atomic_rollback` — si falla CashMovement → todo revertido
- [ ] `test_credit_freezes_exchange_rate` — TC guardado en el acuerdo
- [ ] `test_credit_creates_reservation` — InventoryMovement(RESERVATION) creado
- [ ] `test_credit_audit_log_has_all_terms` — AuditLog tiene términos completos del crédito

---

#### #F05-19 — Tests de pago de cuotas
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-06

**Tareas:**
- [ ] `test_partial_payment_updates_installment` — pago parcial actualiza paid_amount y remaining_amount
- [ ] `test_full_payment_marks_installment_paid` — pago completo → PAID
- [ ] `test_payment_idempotency` — mismo idempotency_key dos veces → 1 CashMovement
- [ ] `test_last_installment_completes_credit` — última cuota → acuerdo PAID, venta COMPLETED
- [ ] `test_advance_payment_multiple_installments` — pago adelantado de 3 cuotas registrado correctamente
- [ ] `test_payment_includes_mora_amount` — pago incluye mora acumulada

---

#### #F05-20 — Tests de mora
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-08, #F05-09

**Tareas:**
- [ ] `test_mora_applied_to_overdue_installment` — mora = 3% de remaining_amount
- [ ] `test_mora_not_capitalized` — mora del mes 2 no incluye mora del mes 1
- [ ] `test_mora_idempotent` — tarea ejecutada 2 veces en el mismo período → 1 sola CreditMora
- [ ] `test_mora_rate_from_settings` — tasa de mora viene de configuración del sistema
- [ ] `test_mora_uses_decimal_not_float` — cálculo usa Decimal, resultado exacto
- [ ] `test_mora_does_not_apply_to_current_period` — mora solo para períodos vencidos

---

#### #F05-21 — Tests de reprogramación
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-10

**Tareas:**
- [ ] `test_owner_can_restructure_installment`
- [ ] `test_sales_cannot_restructure` → 403
- [ ] `test_restructure_saves_original_due_date`
- [ ] `test_restructure_creates_audit_log_with_reason`

---

#### #F05-22 — Tests de entrega anticipada
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-11

**Tareas:**
- [ ] `test_deliver_on_credit_changes_inventory_status`
- [ ] `test_deliver_on_credit_serial_unit_status_updated`
- [ ] `test_complete_all_installments_marks_unit_sold`
- [ ] `test_delivered_on_credit_not_available_for_sale`

---

### DOCUMENTACIÓN

---

#### #F05-23 — Documentar reglas de crédito
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar todas las reglas de validación pre-crédito en `docs/business-rules.md`
- [ ] Documentar el cálculo de mora con ejemplos numéricos
- [ ] Documentar los estados del crédito y sus transiciones
- [ ] Documentar qué pasa con el inventario en cada etapa del crédito
- [ ] Incluir ejemplos: crédito de S/2500, inicial S/500, 4 cuotas, 2 meses gracia, 3% después

---

### VERIFICACIÓN FINAL

---

#### #F05-29 — Seeds completos de créditos
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F05-16

**Tareas:**
- [ ] Ejecutar seed completo → créditos ficticios creados con cuotas correctas
- [ ] Verificar que la mora del seed está calculada correctamente
- [ ] Verificar que el stock reservado corresponde a los créditos activos

---

#### #F05-30 — Verificación final de FASE 05
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Cliente moroso bloqueado automáticamente para nuevos créditos
- [ ] Superación de límite de crédito requiere autorización OWNER
- [ ] Múltiples créditos activos requieren autorización OWNER
- [ ] Crédito crea cuotas correctas con fechas y montos
- [ ] Meses de gracia aplicados correctamente
- [ ] Pago parcial actualiza remaining_amount correctamente
- [ ] Pago adelantado registra cada cuota afectada individualmente
- [ ] Mora al 3% sin capitalizar sobre mora anterior
- [ ] Tarea Celery de mora es idempotente
- [ ] Entrega anticipada mueve a DELIVERED_ON_CREDIT
- [ ] Al pagar todo → SOLD en inventario
- [ ] Todos los tests financieros pasan con precisión Decimal
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §13 Créditos y Cuotas*
*Fase anterior: [FASE 04](FASE-04-caja-pos-ventas.md) | Siguiente fase: [FASE 06](FASE-06-cotizaciones-whatsapp.md)*
