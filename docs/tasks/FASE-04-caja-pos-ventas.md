# FASE 04 — Caja, POS y Ventas

**Rama:** `feature/fase-04-ventas`
**Objetivo:** Operación financiera diaria completa. Caja con sesiones, POS, ventas al contado, descuentos autorizados, cierre con diferencia y transferencias entre cajas.
**Prerrequisito:** FASE 03 completada y mergeada a `develop`.
**Criterio de salida:** Venta al contado es atómica (sale + pago + caja + inventario + audit). Cierre de caja con diferencia requiere aprobación OWNER. Todos los tests financieros críticos pasan.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 32 | 0% |

---

## Issues

### CAJA

---

#### #F04-01 — Modelos de Caja con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-03 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/cash/domain/models.py`:
  ```
  CashRegister:
    id (UUID, PK)
    name (VARCHAR, not null)
    user_id (UUID, FK → User)        — propietario asignado
    is_general (BOOLEAN, default False)  — True solo para caja del OWNER
    active (BOOLEAN, default True)
    created_at (TIMESTAMPTZ)

  CashSession:
    id (UUID, PK)
    register_id (UUID, FK → CashRegister)
    user_id (UUID, FK → User)        — quien abrió la sesión
    status (ENUM): OPEN / PENDING_CLOSURE / CLOSED
    opening_amount (NUMERIC(14,2))
    expected_cash (NUMERIC(14,2))    — calculado por sistema al cierre
    counted_cash (NUMERIC(14,2))     — ingresado por usuario al cierre
    difference (NUMERIC(14,2))       — counted - expected
    opened_at (TIMESTAMPTZ)
    closed_at (TIMESTAMPTZ)
    opened_by (UUID, FK → User)
    closed_by (UUID, FK → User)
    UNIQUE: (user_id, status) WHERE status = 'OPEN'  — solo 1 sesión abierta por usuario

  CashMovement:
    id (UUID, PK)
    session_id (UUID, FK → CashSession)
    type (ENUM): SALE_INCOME/CREDIT_PAYMENT/REPAIR_PAYMENT/
                 INSTALLATION_PAYMENT/QUOTE_PAYMENT/
                 TRANSFER_IN/TRANSFER_OUT/OTHER_INCOME/EXPENSE/OPENING
    amount (NUMERIC(14,2), not null)   — siempre positivo
    direction (ENUM): IN / OUT
    reference_type (VARCHAR)           — sale / credit_payment / repair / manual
    reference_id (UUID)
    reason (TEXT)
    authorized_by (UUID, FK → User)    — para movimientos manuales
    idempotency_key (VARCHAR, unique)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

  CashTransfer:
    id (UUID, PK)
    from_session_id (UUID, FK → CashSession)
    to_session_id (UUID, FK → CashSession)
    amount (NUMERIC(14,2), not null)
    reason (TEXT)
    out_movement_id (UUID, FK → CashMovement)
    in_movement_id (UUID, FK → CashMovement)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

  CashClosureRequest:
    id (UUID, PK)
    session_id (UUID, FK → CashSession)
    expected_cash (NUMERIC(14,2))
    counted_cash (NUMERIC(14,2))
    difference (NUMERIC(14,2))
    status (ENUM): PENDING / APPROVED / REJECTED
    requested_by (UUID, FK → User)
    reviewed_by (UUID, FK → User)
    review_reason (TEXT)
    requested_at (TIMESTAMPTZ)
    reviewed_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic para todas las tablas de caja
- [ ] Constraint UNIQUE parcial en CashSession: solo 1 sesión OPEN por usuario
- [ ] Constraint: `amount > 0` en CashMovement
- [ ] Constraint: `difference = counted_cash - expected_cash` (CHECK)

**Definición de terminado:**
- [ ] Tablas creadas con todos los constraints
- [ ] Test: intentar abrir segunda sesión con una ya abierta → error de constraint

---

#### #F04-02 — Servicio de apertura y gestión de sesión de caja
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-01

**Tareas:**
- [ ] Crear `apps/api/app/modules/cash/application/service.py`:
  - `open_session(register_id, opening_amount, user)`:
    - Verificar que el usuario no tiene sesión OPEN
    - Crear CashSession(OPEN)
    - CashMovement(OPENING, +opening_amount)
    - AuditLog: `OPEN_CASH_SESSION`
  - `get_active_session(user_id)` → CashSession | None
  - `get_session_balance(session_id)`:
    - `SUM(amount) WHERE direction=IN` - `SUM(amount) WHERE direction=OUT`
    - Retorna balance esperado en efectivo
  - `add_movement(session_id, type, amount, direction, reference, reason, user)`:
    - Verificar sesión está OPEN
    - Verificar idempotency_key si se provee
    - Crear CashMovement
    - AuditLog si es movimiento manual
- [ ] Endpoints:
  - `POST /api/v1/cash/sessions/open` — abrir sesión
  - `GET /api/v1/cash/sessions/active` — sesión activa del usuario actual
  - `GET /api/v1/cash/sessions/{id}` — detalle de sesión
  - `GET /api/v1/cash/sessions/{id}/movements` — movimientos de la sesión
  - `GET /api/v1/cash/sessions` — todas las sesiones (solo OWNER, con filtros)

**Definición de terminado:**
- [ ] Solo 1 sesión OPEN por usuario en cualquier momento
- [ ] Balance calculado correctamente como suma de movimientos

---

#### #F04-03 — Flujo de cierre de caja
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-02

**Descripción:**
El cierre con diferencia es una operación crítica que requiere aprobación del OWNER.

**Tareas:**
- [ ] Implementar `request_close_session(session_id, counted_cash, user)`:
  ```
  expected = get_session_balance(session_id)
  difference = counted_cash - expected
  CashSession.expected_cash = expected
  CashSession.counted_cash = counted_cash
  CashSession.difference = difference

  SI difference == 0:
    → CashSession.status = CLOSED
    → CashSession.closed_at = now()
    → AuditLog: CLOSE_CASH_SESSION
    → return {status: "closed"}

  SI difference != 0:
    → CashSession.status = PENDING_CLOSURE
    → Crear CashClosureRequest(PENDING)
    → Notification al OWNER (alta prioridad)
    → return {status: "pending_approval", request_id: ...}
  ```
- [ ] Implementar `approve_closure(request_id, reason, approved_by)` (solo OWNER):
  - CashClosureRequest.status = APPROVED
  - CashSession.status = CLOSED
  - AuditLog: `APPROVE_CASH_CLOSURE` con diferencia y motivo
- [ ] Implementar `reject_closure(request_id, reason, rejected_by)` (solo OWNER):
  - CashClosureRequest.status = REJECTED
  - CashSession.status = OPEN (vuelve a abierta)
  - Notification al cajero
- [ ] Endpoints:
  - `POST /api/v1/cash/sessions/{id}/close` — solicitar cierre
  - `POST /api/v1/cash/closure-requests/{id}/approve` — aprobar (solo OWNER)
  - `POST /api/v1/cash/closure-requests/{id}/reject` — rechazar (solo OWNER)
  - `GET /api/v1/cash/closure-requests` — lista de solicitudes pendientes (solo OWNER)

**Definición de terminado:**
- [ ] Diferencia = 0 → cierre inmediato
- [ ] Diferencia != 0 → solicitud creada, sesión en PENDING_CLOSURE
- [ ] OWNER aprueba con motivo → sesión CLOSED, AuditLog con diferencia y motivo
- [ ] OWNER rechaza → sesión vuelve a OPEN

---

#### #F04-04 — Transferencias entre cajas
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-02

**Tareas:**
- [ ] Implementar `transfer_between_sessions(from_id, to_id, amount, reason, user)` (solo OWNER):
  ```
  [TRANSACCIÓN ATÓMICA]:
    - Verificar que ambas sesiones están OPEN
    - Verificar que from tiene saldo suficiente
    - CashMovement(TRANSFER_OUT, -amount) en from_session
    - CashMovement(TRANSFER_IN, +amount) en to_session
    - CashTransfer creado vinculando ambos movimientos
    - AuditLog: TRANSFER_CASH
  SI CUALQUIER PARTE FALLA: ROLLBACK TOTAL
  ```
- [ ] Endpoint: `POST /api/v1/cash/transfers`
- [ ] Test de rollback: simular fallo después del primer movimiento → ambas cajas sin cambios

**Definición de terminado:**
- [ ] Transferencia exitosa → ambos movimientos creados en misma transacción
- [ ] Fallo a mitad → ROLLBACK, ninguna caja afectada
- [ ] Solo OWNER puede transferir → 403 si SALES intenta

---

#### #F04-05 — Ingresos y egresos manuales
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-02

**Tareas:**
- [ ] Endpoint `POST /api/v1/cash/sessions/{id}/income` — ingreso manual (solo OWNER):
  - Campos: amount, reason, reference (opcional)
  - CashMovement(OTHER_INCOME, direction=IN)
  - AuditLog
- [ ] Endpoint `POST /api/v1/cash/sessions/{id}/expense` — egreso (solo OWNER):
  - Campos: amount, reason, reference (opcional)
  - CashMovement(EXPENSE, direction=OUT)
  - AuditLog
- [ ] Ambos requieren `reason` no vacío

---

### DESCUENTOS

---

#### #F04-06 — Modelo y flujo de autorización de descuentos
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-03 completa

**Tareas:**
- [ ] Crear modelo `DiscountAuthorization`:
  ```
  DiscountAuthorization:
    id (UUID, PK)
    sale_id (UUID, FK → Sale, nullable)  — puede ser pre-venta
    type (ENUM): PERCENTAGE / FIXED_AMOUNT
    percentage (NUMERIC(5,4))
    fixed_amount (NUMERIC(14,2))
    reason (TEXT, not null)
    requested_by (UUID, FK → User)
    approved_by (UUID, FK → User)
    status (ENUM): PENDING / APPROVED / REJECTED
    requested_at (TIMESTAMPTZ)
    reviewed_at (TIMESTAMPTZ)
    CONSTRAINT: percentage >= 0 AND percentage <= 1
    CONSTRAINT: fixed_amount >= 0
  ```
- [ ] Migración
- [ ] Endpoints:
  - `POST /api/v1/discounts/request` — SALES solicita descuento
  - `POST /api/v1/discounts/{id}/approve` — OWNER aprueba
  - `POST /api/v1/discounts/{id}/reject` — OWNER rechaza
  - `GET /api/v1/discounts/pending` — lista pendientes (solo OWNER)
- [ ] OWNER puede crear descuento directamente sin solicitud (status=APPROVED automático)
- [ ] Constraint: descuento negativo imposible (error 400)
- [ ] AuditLog para toda aprobación/rechazo de descuento

**Definición de terminado:**
- [ ] SALES solicita descuento → notificación a OWNER
- [ ] OWNER aprueba/rechaza → notificación a SALES
- [ ] Descuento negativo → 400
- [ ] AuditLog registra aprobación con quién autorizó

---

### VENTAS

---

#### #F04-07 — Modelos Sale, SaleItem, SalePayment con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-01, #F04-06

**Tareas:**
- [ ] Crear `apps/api/app/modules/sales/domain/models.py`:
  ```
  Sale:
    id (UUID, PK)
    code (VARCHAR, unique)               — VTA-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    sale_type (ENUM): CASH / PARTIAL / CREDIT
    status (ENUM): DRAFT/PENDING_PAYMENT/PARTIALLY_PAID/PAID/CANCELLED/RETURNED/COMPLETED
    subtotal (NUMERIC(14,2))
    discount_amount (NUMERIC(14,2), default 0)
    total (NUMERIC(14,2))
    currency (VARCHAR(3))
    exchange_rate (NUMERIC(10,4))        — CONGELADO al crear
    exchange_rate_source (VARCHAR)
    exchange_rate_timestamp (TIMESTAMPTZ)
    discount_authorization_id (UUID, FK → DiscountAuthorization, nullable)
    cash_session_id (UUID, FK → CashSession)
    idempotency_key (VARCHAR, unique)
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  SaleItem:
    id (UUID, PK)
    sale_id (UUID, FK → Sale)
    product_id (UUID, FK → Product)
    serialized_unit_id (UUID, FK → SerializedUnit, nullable)
    quantity (NUMERIC(14,3))
    unit_price (NUMERIC(14,2))           — precio AL MOMENTO de la venta
    unit_cost (NUMERIC(14,2))            — costo AL MOMENTO (para margen)
    discount_amount (NUMERIC(14,2), default 0)
    subtotal (NUMERIC(14,2))

  SalePayment:
    id (UUID, PK)
    sale_id (UUID, FK → Sale)
    method (ENUM): CASH/YAPE/PLIN/CARD/BANK_TRANSFER/OTHER
    method_detail (VARCHAR)              — si method = OTHER
    amount (NUMERIC(14,2))
    reference (VARCHAR)                  — nro. operación, voucher
    idempotency_key (VARCHAR, unique)
    paid_at (TIMESTAMPTZ)
    registered_by (UUID, FK → User)
  ```
- [ ] Migración Alembic
- [ ] Constraints: `total >= 0`, `discount_amount >= 0`, `quantity > 0`

---

#### #F04-08 — Servicio de ventas al contado (operación atómica)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-07, #F03-03

**Descripción:**
La venta al contado es la operación financiera más crítica. Debe ser completamente atómica.

**Tareas:**
- [ ] Crear `apps/api/app/modules/sales/application/service.py`:
  - `create_cash_sale(items, payment, customer_id, discount_auth_id, session_id, idempotency_key, user)`:
    ```
    [TRANSACCIÓN ATÓMICA - TODO O NADA]:
    1. Verificar idempotency_key (si ya existe, retornar resultado anterior)
    2. Obtener tipo de cambio vigente (congela en la venta)
    3. Para cada item:
       a. SELECT product FOR UPDATE (lock)
       b. Si serializado: SELECT serialized_unit FOR UPDATE
       c. Verificar stock disponible >= quantity
    4. Si discount_auth_id: verificar que está APPROVED
    5. Calcular subtotal, descuento, total
    6. Crear Sale(status=DRAFT)
    7. Crear SaleItem × N
    8. Crear SalePayment
    9. Verificar payment.amount >= sale.total (o configurar si acepta saldo)
    10. Sale.status = PAID
    11. CashMovement(SALE_INCOME, IN) en cash_session
    12. Por cada item:
        - InventoryMovement(SALE, -qty)
        - Si serializado: SerializedUnit.status = SOLD
    13. AuditLog: CREATE_SALE
    SI CUALQUIER PASO FALLA: ROLLBACK
    ```
- [ ] Endpoints:
  - `POST /api/v1/sales` — crear venta
  - `GET /api/v1/sales` — lista con filtros (fecha, estado, tipo, cliente, vendedor)
  - `GET /api/v1/sales/{id}` — detalle completo
  - `POST /api/v1/sales/{id}/payments` — registrar pago adicional
  - `POST /api/v1/sales/{id}/cancel` — cancelar (OWNER o SALES con autorización)

**Definición de terminado:**
- [ ] Venta exitosa → Sale=PAID + CashMovement + InventoryMovement × N + AuditLog en una sola transacción
- [ ] Si falla el CashMovement → ROLLBACK completo (Sale no creada)
- [ ] Doble envío con mismo idempotency_key → retorna primera venta sin duplicar
- [ ] SALES no puede vender si no tiene sesión de caja abierta → 400

---

#### #F04-09 — Generador de código de venta
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-07

**Tareas:**
- [ ] Crear tabla `document_sequences` (si no existe del módulo de SKU):
  ```
  document_sequences:
    prefix (VARCHAR, PK)
    year (INTEGER)
    last_value (INTEGER)
    PK: (prefix, year)
  ```
- [ ] Función `generate_document_code(prefix, session)` — VTA-2026-00001, OC-2026-00001, etc.
- [ ] Reutilizable para todos los módulos (reparaciones, compras, cotizaciones, etc.)
- [ ] Transaccional con `SELECT FOR UPDATE`

---

#### #F04-10 — Cancelación de ventas
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-08

**Tareas:**
- [ ] `cancel_sale(sale_id, reason, authorization_id, user)`:
  - Solo si status IN (DRAFT, PENDING_PAYMENT, PARTIALLY_PAID)
  - OWNER cancela directo
  - SALES debe tener CancellationAuthorization (igual que descuento)
  - Si ya hay InventoryMovements: generar movimientos inversos (devolución de stock)
  - Si ya hay CashMovements: generar ajuste de caja
  - Sale.status = CANCELLED (nunca borrar)
  - AuditLog: CANCEL_SALE con motivo
- [ ] Endpoint: `POST /api/v1/sales/{id}/cancel`

---

### POS

---

#### #F04-11 — Interfaz POS (punto de venta)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-08

**Descripción:**
El POS es la interfaz principal de ventas. Debe ser rápido, simple y funcionar con teclado.

**Tareas:**
- [ ] Crear `apps/web/app/admin/pos/page.tsx` con layout especial (sin sidebar, pantalla completa)
- [ ] Sección izquierda: búsqueda y selección de productos
  - Búsqueda por nombre, SKU o código de barras (autofocus al cargar)
  - Soporte para lector de código de barras (Enter dispara búsqueda)
  - Tarjetas de productos con precio actual (con oferta si aplica)
- [ ] Sección derecha: carrito actual
  - Lista de ítems con cantidad (editable), precio unitario, subtotal
  - Eliminar ítem
  - Campo de descuento (si tiene permiso o hay autorización)
  - Total prominente en pantalla
  - Selector de cliente (buscar por nombre/DNI, o "cliente genérico")
- [ ] Sección de pago:
  - Selector de método de pago (CASH, YAPE, PLIN, CARD, TRANSFER, OTHER)
  - Campo de monto recibido (para calcular vuelto en efectivo)
  - Botón "Cobrar" grande y visible
  - Indicador de sesión de caja activa
- [ ] Al completar venta:
  - Modal de éxito con resumen
  - Opción de imprimir/compartir comprobante (preparar, implementar en FASE 12)
  - Auto-limpiar carrito para siguiente venta
- [ ] Modo offline básico: si no hay conexión, mostrar alerta visible (no permitir venta sin conexión para garantizar integridad)

**Definición de terminado:**
- [ ] Venta completa desde POS en menos de 10 segundos
- [ ] Búsqueda por código de barras funciona
- [ ] Sin sesión de caja abierta → alerta y botón para abrir sesión

---

#### #F04-12 — Apertura y cierre de caja en frontend
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-03

**Tareas:**
- [ ] `apps/web/app/admin/caja/page.tsx` — vista de caja del usuario actual:
  - Estado: OPEN / CLOSED / PENDING_CLOSURE
  - Si CLOSED: botón "Abrir Caja" con campo de monto inicial
  - Si OPEN: resumen de movimientos del día (ingresos, egresos, balance)
  - Listado de movimientos de la sesión actual
  - Botón "Cerrar Caja" → modal de conteo
- [ ] Modal de cierre:
  - Campo "Efectivo contado" (ingresado por el usuario)
  - El sistema muestra "Efectivo esperado" calculado
  - Si hay diferencia: alerta visual clara antes de confirmar
  - Botón "Solicitar cierre" (si hay diferencia) o "Cerrar ahora" (si no hay)
- [ ] `apps/web/app/admin/caja/solicitudes/page.tsx` — solicitudes de cierre (solo OWNER):
  - Lista de solicitudes PENDING con diferencia destacada
  - Formulario de aprobación/rechazo con motivo obligatorio
- [ ] `apps/web/app/admin/caja/general/page.tsx` — vista de todas las cajas (solo OWNER)

---

#### #F04-13 — Vista de ventas (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-08

**Tareas:**
- [ ] `apps/web/app/admin/ventas/page.tsx` — tabla de ventas con filtros
- [ ] Filtros: fecha, tipo (CASH/PARTIAL/CREDIT), estado, cliente, vendedor
- [ ] Indicadores: badge de estado con colores
- [ ] `apps/web/app/admin/ventas/[id]/page.tsx` — detalle:
  - Información de la venta, cliente, ítems
  - Timeline de pagos
  - Historial de estados
  - Botón de cancelar (si aplica)
- [ ] SALES solo ve sus propias ventas

---

### SEEDS

---

#### #F04-14 — Seeds de cajas y ventas ficticias
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-08

**Tareas:**
- [ ] Seed de cajas: una caja general (OWNER) + caja para usuario SALES
- [ ] Seed de sesiones cerradas con movimientos ficticios
- [ ] Seed de 10-15 ventas ficticias (contado) con diferentes métodos de pago
- [ ] Seed de 2-3 ventas canceladas con razón
- [ ] Todos los datos son ficticios, ningún dato real

---

### TESTS FINANCIEROS CRÍTICOS

---

#### #F04-15 — Tests de venta al contado
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-08

**Tareas:**
- [ ] `test_cash_sale_atomic` — venta exitosa crea Sale + SalePayment + CashMovement + InventoryMovement en una transacción
- [ ] `test_cash_sale_rollback_on_cash_failure` — si CashMovement falla → ROLLBACK (Sale no existe)
- [ ] `test_cash_sale_rollback_on_inventory_failure` — si InventoryMovement falla → ROLLBACK
- [ ] `test_cash_sale_insufficient_stock` → 400, nada creado
- [ ] `test_cash_sale_idempotency` — mismo idempotency_key dos veces → 1 sola venta, 1 solo CashMovement
- [ ] `test_cash_sale_freezes_exchange_rate` — venta guarda TC actual, no el del día siguiente
- [ ] `test_cash_sale_audit_log_created` — AuditLog con todos los detalles

---

#### #F04-16 — Tests de caja
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-03

**Tareas:**
- [ ] `test_open_session_success` → CashSession(OPEN) creada
- [ ] `test_cannot_open_two_sessions` → 409 al intentar segunda sesión
- [ ] `test_close_session_no_difference` → cierre inmediato, status=CLOSED
- [ ] `test_close_session_with_difference_creates_request` → CashClosureRequest(PENDING) creada
- [ ] `test_approve_closure_closes_session` → CashSession(CLOSED), AuditLog con motivo
- [ ] `test_reject_closure_reopens_session` → CashSession vuelve a OPEN
- [ ] `test_sales_cannot_see_other_sessions` → 403
- [ ] `test_close_requires_owner_approval_when_difference` — SALES no puede auto-aprobar → 403

---

#### #F04-17 — Tests de transferencia de caja
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-04

**Tareas:**
- [ ] `test_transfer_creates_both_movements_atomically` — ambos CashMovement creados
- [ ] `test_transfer_rollback_if_second_movement_fails` — si falla IN → OUT también revertido
- [ ] `test_transfer_updates_both_balances` — from baja, to sube por el mismo monto
- [ ] `test_only_owner_can_transfer` → 403 para SALES
- [ ] `test_transfer_insufficient_balance` → 400

---

#### #F04-18 — Tests de descuentos
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-06, #F04-08

**Tareas:**
- [ ] `test_owner_applies_discount_directly` → descuento aplicado sin solicitud
- [ ] `test_sales_cannot_apply_discount_without_authorization` → 403
- [ ] `test_sales_requests_discount_owner_approves` → venta creada con descuento
- [ ] `test_negative_discount_rejected` → 400
- [ ] `test_discount_over_100_percent_rejected` → 400
- [ ] `test_discount_audit_log_includes_approver` — AuditLog tiene `approved_by`

---

#### #F04-19 — Tests de cancelación de venta
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-10

**Tareas:**
- [ ] `test_cancel_sale_restores_stock` — inventario vuelve a disponible
- [ ] `test_cancel_sale_does_not_delete_record` — Sale existe con status=CANCELLED
- [ ] `test_cancel_sale_creates_audit_log`
- [ ] `test_cannot_cancel_completed_sale` → 409

---

### DOCUMENTACIÓN

---

#### #F04-20 — Documentar flujos financieros
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar el flujo completo de venta al contado en `docs/business-rules.md`
- [ ] Documentar el flujo de cierre de caja en `docs/business-rules.md`
- [ ] Documentar la estrategia de idempotencia en `docs/architecture.md`
- [ ] Documentar los tipos de movimiento de caja y cuándo se usan

---

#### #F04-21 — Módulo de clientes básico (necesario para ventas)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-03 completa

**Descripción:**
Se necesita el modelo Customer para crear ventas. Implementar el CRUD completo aquí.

**Tareas:**
- [ ] Crear `apps/api/app/modules/customers/domain/models.py`:
  ```
  Customer:
    id (UUID, PK)
    user_id (UUID, FK → User, nullable)
    type (ENUM): PERSON / COMPANY
    first_name, last_name (VARCHAR)
    razon_social (VARCHAR, nullable)
    dni (VARCHAR, unique, nullable)
    ruc (VARCHAR, unique, nullable)
    phone (VARCHAR)
    phone_whatsapp (VARCHAR)
    email (VARCHAR)
    address (TEXT)
    district, city (VARCHAR)
    credit_limit (NUMERIC(14,2), default 0)
    is_blocked (BOOLEAN, default False)
    block_reason (TEXT)
    is_frequent (BOOLEAN, default False)
    notes (TEXT)
    active (BOOLEAN, default True)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] CRUD completo con búsqueda por nombre, DNI, RUC, teléfono
- [ ] Seed de 10 clientes ficticios
- [ ] Endpoints:
  - `GET /api/v1/customers` — lista (OWNER y SALES)
  - `POST /api/v1/customers` — crear (OWNER y SALES)
  - `GET /api/v1/customers/{id}` — detalle
  - `PUT /api/v1/customers/{id}` — actualizar
  - `GET /api/v1/customers/search?q=` — búsqueda rápida para POS

---

#### #F04-22 — Frontend de clientes (básico)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-21

**Tareas:**
- [ ] `apps/web/app/admin/clientes/page.tsx` — tabla con búsqueda
- [ ] `apps/web/app/admin/clientes/nuevo/page.tsx` — formulario de creación
- [ ] `apps/web/app/admin/clientes/[id]/page.tsx` — detalle (con historial de compras, preparar secciones de créditos/reparaciones para fases posteriores)

---

### VERIFICACIÓN FINAL

---

#### #F04-23 — Seeds completos de fase 04
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-14

**Tareas:**
- [ ] Ejecutar seed completo (FASE00 a FASE04) sin errores
- [ ] Verificar que el sistema tiene: usuarios, productos con stock, clientes, cajas y ventas ficticias
- [ ] Verificar que el balance de caja es coherente con las ventas ficticias

---

#### #F04-24 — Preparar módulo de devoluciones (estructura)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-07

**Descripción:**
Crear los modelos de devolución ahora (se necesitan para ventas) aunque el flujo completo va en FASE 09.

**Tareas:**
- [ ] Crear modelos Return y ReturnItem con migración
- [ ] No implementar el flujo completo todavía (marcado como TODO documentado)
- [ ] El modelo solo debe existir para poder hacer referencias desde Sale

---

#### #F04-31 — Verificación final de FASE 04
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Venta al contado: atómica, todos los movimientos creados
- [ ] Doble venta con mismo idempotency_key → 1 resultado sin duplicar
- [ ] POS funcional y usable
- [ ] Apertura y cierre de caja funcionan
- [ ] Cierre con diferencia requiere aprobación OWNER
- [ ] Transferencia entre cajas es atómica
- [ ] SALES no puede ver cajas ajenas → 403
- [ ] Descuento de SALES requiere autorización → 403 sin ella
- [ ] Cambios de precio registrados en AuditLog
- [ ] Todos los tests de esta fase pasan
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

#### #F04-32 — Tests de concurrencia de venta
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F04-08

**Tareas:**
- [ ] `test_concurrent_sale_same_serialized_unit` — 2 requests simultáneos del mismo serial → 1 ok, 1 error
- [ ] `test_concurrent_sale_limited_stock` — 10 requests con stock=5 → exactamente 5 ventas, 5 errores
- [ ] Usar `asyncio.gather` o threads para simular concurrencia real en tests

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §11 Ventas, §12 Caja, §22 Clientes*
*Fase anterior: [FASE 03](FASE-03-inventario-compras.md) | Siguiente fase: [FASE 05](FASE-05-creditos-cuotas-mora.md)*
