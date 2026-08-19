# FASE 03 — Inventario y Compras

**Rama:** `feature/fase-03-inventario`
**Objetivo:** Inventario real basado en movimientos (nunca stock como campo editable). Gestión completa de proveedores y órdenes de compra.
**Prerrequisito:** FASE 02 completada y mergeada a `develop`.
**Criterio de salida:** Stock calculado correctamente por movimientos, compras generan InventoryMovements, kardex funcional, concurrencia de stock probada.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 20 | 0% |

---

## Issues

### INVENTARIO

---

#### #F03-01 — Modelo InventoryMovement con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-02 completa

**Descripción:**
El stock NUNCA es un campo. El stock es la suma algebraica de los movimientos. Esta tabla es el corazón del inventario.

**Tareas:**
- [ ] Crear `apps/api/app/modules/inventory/domain/models.py`:
  ```
  InventoryMovement:
    id (UUID, PK)
    product_id (UUID, FK → Product, not null)
    serialized_unit_id (UUID, FK → SerializedUnit, nullable)
    quantity (NUMERIC(14,3), not null)     — positivo = entrada, negativo = salida
    movement_type (ENUM, not null):
      PURCHASE / SALE / RESERVATION / RELEASE_RESERVATION /
      PARTIAL_PAYMENT_HOLD / CREDIT_DELIVERY / SALE_COMPLETED /
      RETURN / ADJUSTMENT_IN / ADJUSTMENT_OUT /
      REPAIR_USAGE / REPAIR_RETURN / DAMAGED / TRANSFER
    reference_type (VARCHAR)               — sale / purchase / repair / adjustment / transfer
    reference_id (UUID)                    — ID del documento origen
    warehouse (VARCHAR, default 'principal')
    unit_cost (NUMERIC(14,2))              — costo al momento del movimiento
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ, not null)

  INDEXes:
    (product_id, created_at DESC)          — para calcular stock
    (reference_type, reference_id)         — para trazabilidad
    (movement_type, created_at)            — para kardex filtrado
  ```
- [ ] Migración Alembic para `inventory_movements`
- [ ] Constraint: movimientos de tipo ADJUSTMENT_* requieren `authorization_id` (FK → AuditLog)
- [ ] Los movimientos son **INMUTABLES** — no existe UPDATE ni DELETE en el repositorio

**Definición de terminado:**
- [ ] Tabla creada con todos los índices
- [ ] No existe método `update` ni `delete` en el repositorio de inventario

---

#### #F03-02 — Cálculo de stock disponible
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-01

**Descripción:**
Función que calcula el stock en tiempo real sumando movimientos. Nunca leer un campo `stock`.

**Tareas:**
- [ ] Crear función `get_stock_summary(product_id, session) -> StockSummary`:
  ```python
  StockSummary:
    available: Decimal       # PURCHASE + ADJUSTMENT_IN + RETURN + REPAIR_RETURN
                             # - SALE - ADJUSTMENT_OUT - REPAIR_USAGE - DAMAGED
                             # (excluyendo reservas y créditos)
    reserved: Decimal        # RESERVATION - RELEASE_RESERVATION
    partially_paid: Decimal  # PARTIAL_PAYMENT_HOLD
    on_credit: Decimal       # CREDIT_DELIVERY - SALE_COMPLETED
    total_physical: Decimal  # available + reserved + partially_paid + on_credit
  ```
- [ ] La función debe usar una sola query agregada, no múltiples queries
- [ ] Crear Vista PostgreSQL `v_product_stock` que precalcula por producto (para listados masivos)
- [ ] Endpoint: `GET /api/v1/inventory/stock/{product_id}` — stock actual del producto
- [ ] Endpoint: `GET /api/v1/inventory/stock` — stock de todos los productos (paginado)
- [ ] Incluir alerta si `available <= product.stock_minimum`

**Definición de terminado:**
- [ ] Stock calculado correctamente después de compras y ventas de prueba
- [ ] `available` nunca puede ser negativo en la vista
- [ ] Test: crear movimientos de entrada y salida → stock correcto

---

#### #F03-03 — Servicio de inventario con control de concurrencia
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-02

**Descripción:**
Todas las operaciones que modifican inventario deben ser seguras bajo concurrencia.

**Tareas:**
- [ ] Crear `apps/api/app/modules/inventory/application/service.py`:
  - `reserve_stock(product_id, qty, reference_type, reference_id, session)`:
    - `SELECT SUM(quantity) FROM inventory_movements WHERE product_id = :id FOR UPDATE`
    - Verificar que `available >= qty`
    - Si no: lanzar `InsufficientStockError`
    - Crear `InventoryMovement(RESERVATION, -qty)`
    - Todo en la misma transacción del llamador
  - `release_reservation(product_id, qty, reference_id, session)`:
    - Crear `InventoryMovement(RELEASE_RESERVATION, +qty)`
  - `confirm_sale(product_id, qty, reference_id, session)`:
    - Crear `InventoryMovement(SALE, -qty)`
    - Si serializado: actualizar `SerializedUnit.status = SOLD`
  - `register_adjustment(product_id, qty, reason, authorized_by, session)`:
    - Solo con autorización de OWNER
    - `ADJUSTMENT_IN` si qty > 0, `ADJUSTMENT_OUT` si qty < 0
    - AuditLog obligatorio
- [ ] Para `SerializedUnit`: usar `SELECT ... FOR UPDATE` al cambiar estado

**Definición de terminado:**
- [ ] Dos ventas simultáneas del mismo serial → solo una exitosa
- [ ] Test de concurrencia: 5 requests simultáneos con stock=3 → exactamente 3 exitosos, 2 con error
- [ ] Ajuste sin autorización → 403

---

#### #F03-04 — Kardex (historial de movimientos)
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-02

**Tareas:**
- [ ] Endpoint: `GET /api/v1/inventory/kardex/{product_id}` con filtros:
  - Fecha desde/hasta
  - Tipo de movimiento
  - Paginación (por defecto 50 registros)
- [ ] Respuesta incluye para cada movimiento:
  - Fecha, tipo, cantidad, costo, saldo acumulado, documento origen, usuario
- [ ] `GET /api/v1/inventory/kardex/{product_id}/export` — exportar CSV/Excel (preparar, implementar en FASE 12)
- [ ] Frontend: `apps/web/app/admin/inventario/kardex/[id]/page.tsx`
  - Timeline visual de movimientos
  - Filtros por fecha y tipo
  - Saldo running (columna de stock acumulado)

**Definición de terminado:**
- [ ] Kardex muestra todos los movimientos en orden cronológico
- [ ] El saldo acumulado en cada línea es correcto
- [ ] Filtros funcionan correctamente

---

#### #F03-05 — Ajustes manuales de inventario
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-03

**Tareas:**
- [ ] `POST /api/v1/inventory/adjustments` — crear ajuste manual (solo OWNER):
  ```json
  {
    "product_id": "uuid",
    "quantity": 5,
    "reason": "Conteo físico - diferencia de 5 unidades",
    "notes": "Realizado el 2026-08-17"
  }
  ```
- [ ] AuditLog obligatorio con old_values (stock antes) y new_values (stock después)
- [ ] Frontend: modal de ajuste en la vista de inventario con campo de razón obligatorio

---

#### #F03-06 — Vista de inventario (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-02, #F03-04

**Tareas:**
- [ ] Crear `apps/web/app/admin/inventario/page.tsx`
- [ ] Tabla con: producto, SKU, categoría, stock disponible, reservado, en crédito, total
- [ ] Indicadores visuales:
  - 🔴 Agotado (available = 0)
  - 🟠 Stock bajo (available ≤ stock_minimum)
  - 🟢 OK
- [ ] Filtros: categoría, marca, estado de stock, serializado/no serializado
- [ ] Acción: ver kardex, ajustar (solo OWNER)
- [ ] Exportar a Excel (preparar botón, implementar en FASE 12)

---

### PROVEEDORES

---

#### #F03-07 — Módulo de proveedores: modelo y CRUD
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-02 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/suppliers/domain/models.py`:
  ```
  Supplier:
    id (UUID, PK)
    razon_social (VARCHAR, not null)
    ruc (VARCHAR, unique)
    nombre_comercial (VARCHAR)
    contacto_nombre (VARCHAR)
    telefono (VARCHAR)
    telefono_whatsapp (VARCHAR)
    email (VARCHAR)
    direccion (TEXT)
    ciudad (VARCHAR)
    active (BOOLEAN, default True)
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] CRUD completo (solo OWNER):
  - `GET /api/v1/suppliers` — lista paginada con búsqueda
  - `POST /api/v1/suppliers` — crear
  - `GET /api/v1/suppliers/{id}` — detalle
  - `PUT /api/v1/suppliers/{id}` — actualizar
  - `DELETE /api/v1/suppliers/{id}` — desactivar (no eliminar)

**Definición de terminado:**
- [ ] CRUD funciona con permisos correctos (solo OWNER)
- [ ] SALES intenta crear proveedor → 403

---

### COMPRAS

---

#### #F03-08 — Modelo Purchase y PurchaseItem con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-07

**Tareas:**
- [ ] Crear modelos:
  ```
  Purchase:
    id (UUID, PK)
    code (VARCHAR, unique)       — OC-YYYY-XXXXX
    supplier_id (UUID, FK → Supplier)
    status (ENUM): DRAFT/ORDERED/RECEIVED/PARTIAL/CANCELLED
    total (NUMERIC(14,2))
    currency (VARCHAR(3))
    exchange_rate (NUMERIC(10,4))
    exchange_rate_source (VARCHAR)
    invoice_number (VARCHAR)     — factura del proveedor
    invoice_file_id (UUID, FK → FileObject, nullable)
    received_at (TIMESTAMPTZ)
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  PurchaseItem:
    id (UUID, PK)
    purchase_id (UUID, FK → Purchase)
    product_id (UUID, FK → Product)
    quantity (NUMERIC(14,3), not null)
    unit_cost (NUMERIC(14,2), not null)
    subtotal (NUMERIC(14,2), not null)     — quantity * unit_cost
    received_quantity (NUMERIC(14,3), default 0)
    notes (TEXT)
  ```
- [ ] Migración Alembic

---

#### #F03-09 — Flujo de compra: creación y recepción
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-08, #F03-03

**Descripción:**
La recepción de una compra es una operación atómica que genera movimientos de inventario.

**Tareas:**
- [ ] Crear `apps/api/app/modules/purchases/application/service.py`:
  - `create_purchase(data, created_by)` — crea Purchase(DRAFT) con ítems
  - `confirm_order(purchase_id, user)` — DRAFT → ORDERED
  - `receive_purchase(purchase_id, received_items, user)`:
    ```
    [TRANSACCIÓN ATÓMICA]:
      - Actualizar received_quantity en cada PurchaseItem
      - Si todos recibidos: Purchase.status = RECEIVED
      - Si parcial: Purchase.status = PARTIAL
      - InventoryMovement(PURCHASE, +qty) por cada ítem recibido
      - Si producto es serializado: crear/actualizar SerializedUnit
      - Opcionalmente actualizar cost_price del producto
      - AuditLog
    ```
  - `cancel_purchase(purchase_id, reason, user)` — solo si no está RECEIVED
- [ ] Endpoints:
  - `GET /api/v1/purchases` — lista (solo OWNER)
  - `POST /api/v1/purchases` — crear (solo OWNER)
  - `GET /api/v1/purchases/{id}` — detalle
  - `PUT /api/v1/purchases/{id}` — editar si DRAFT
  - `POST /api/v1/purchases/{id}/confirm` — confirmar pedido
  - `POST /api/v1/purchases/{id}/receive` — registrar recepción
  - `POST /api/v1/purchases/{id}/cancel` — cancelar
  - `POST /api/v1/purchases/{id}/upload-invoice` — subir factura del proveedor

**Definición de terminado:**
- [ ] Recepción de compra crea InventoryMovements correctos
- [ ] Stock aumenta después de recibir compra
- [ ] No se puede cancelar una compra ya recibida → 409
- [ ] AuditLog registra recepción de compra

---

#### #F03-10 — Frontend de compras y proveedores
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-09

**Tareas:**
- [ ] `apps/web/app/admin/proveedores/page.tsx` — lista con búsqueda
- [ ] `apps/web/app/admin/proveedores/[id]/page.tsx` — detalle con historial de compras
- [ ] `apps/web/app/admin/compras/page.tsx` — lista con filtros por estado y proveedor
- [ ] `apps/web/app/admin/compras/nueva/page.tsx` — formulario:
  - Seleccionar proveedor
  - Agregar ítems (búsqueda de producto por nombre/SKU)
  - Cantidad y costo unitario por ítem
  - Moneda y tipo de cambio
  - Vista previa del total
- [ ] `apps/web/app/admin/compras/[id]/page.tsx` — detalle con estado y botón de recepción
- [ ] Modal de recepción: confirmar cantidades recibidas por ítem

---

### SEEDS

---

#### #F03-11 — Seeds de inventario inicial
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-09

**Tareas:**
- [ ] Crear seed de proveedores ficticios (3-5 proveedores con datos inventados)
- [ ] Crear seed de compras ficticias que generan stock inicial para los productos del seed de FASE 02
- [ ] Al ejecutar el seed completo: productos deben tener stock > 0 y coherente

---

### TESTS

---

#### #F03-12 — Tests de inventario críticos
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-03

**Tareas:**
- [ ] `test_stock_calculated_from_movements` — stock = suma de movimientos
- [ ] `test_stock_cannot_go_negative` — movimiento que genera negativo → error
- [ ] `test_reserve_reduces_available` — reserva reduce disponible pero no total
- [ ] `test_release_reservation_restores_stock` — liberación restaura disponible
- [ ] `test_concurrent_sales_same_stock` — 5 ventas simultáneas con stock=3 → 3 ok, 2 error
- [ ] `test_concurrent_serialized_unit_sale` — 2 ventas del mismo serial → 1 ok, 1 error
- [ ] `test_adjustment_requires_owner` → 403 sin permiso
- [ ] `test_adjustment_creates_audit_log` — ajuste queda en auditoría
- [ ] `test_inventory_movement_immutable` — no existe endpoint de actualización

---

#### #F03-13 — Tests de compras
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-09

**Tareas:**
- [ ] `test_purchase_reception_creates_inventory_movement` — recepción genera movimiento PURCHASE
- [ ] `test_purchase_reception_increases_stock` — stock sube después de recibir
- [ ] `test_partial_reception` — recepción parcial → status PARTIAL
- [ ] `test_cancel_received_purchase_blocked` → 409
- [ ] `test_purchase_in_usd_stores_exchange_rate` — TC guardado en la compra
- [ ] `test_sales_cannot_create_purchase` → 403

---

#### #F03-14 — Tests de kardex
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-04

**Tareas:**
- [ ] `test_kardex_shows_all_movements_in_order` — cronológico
- [ ] `test_kardex_running_balance_correct` — saldo acumulado correcto en cada línea
- [ ] `test_kardex_filter_by_movement_type` — filtro funciona
- [ ] `test_kardex_filter_by_date_range` — filtro de fechas funciona

---

### ALERTAS DE STOCK

---

#### #F03-15 — Tarea Celery: alertas de stock bajo
- **Tipo:** `[TASK]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-02

**Tareas:**
- [ ] Crear tarea `check_low_stock()` en `apps/worker/tasks/notifications.py`:
  - Busca productos con `available <= stock_minimum`
  - Crea `Notification` para el OWNER
  - Si `available = 0`: evento `STOCK_OUT` → WhatsApp al OWNER (cuando módulo WhatsApp esté listo, preparar evento aquí)
  - Si `available > 0` y bajo: evento `STOCK_LOW` → Notification interna
- [ ] Configurar en Beat: ejecutar 2 veces al día (9 AM y 3 PM)
- [ ] La tarea es idempotente: no genera notificaciones duplicadas para el mismo producto en el mismo día

---

### DOCUMENTACIÓN

---

#### #F03-16 — Documentar inventario en docs/
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar el modelo de inventario basado en movimientos en `docs/business-rules.md`
- [ ] Documentar cada tipo de movimiento y cuándo se usa
- [ ] Documentar el cálculo de stock disponible vs. reservado vs. en crédito
- [ ] Documentar el flujo de concurrencia y los locks utilizados

---

### VERIFICACIÓN FINAL

---

#### #F03-17 — Verificación de precisión numérica en inventario
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-02

**Tareas:**
- [ ] Verificar que todos los campos de cantidad usan `Decimal` en Python, nunca `float`
- [ ] Verificar que la suma de movimientos usa `NUMERIC` en SQL, nunca `FLOAT`
- [ ] Test: suma de 100 movimientos de 0.1 unidad = exactamente 10.0 (no 9.999...)

---

#### #F03-18 — Seeds de compras con seriales ficticios
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-11

**Tareas:**
- [ ] Para cada laptop serializada del seed: registrar serial ficticio en el seed de compra
- [ ] SerializedUnit.status = AVAILABLE para todos los seriales del seed

---

#### #F03-19 — Tarea Celery: reporte diario de stock
- **Tipo:** `[TASK]`
- **Prioridad:** 🟢 BAJO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F03-02

**Tareas:**
- [ ] Preparar estructura de tarea `generate_daily_stock_report()` (contenido completo en FASE 12)
- [ ] Programar en Beat para ejecutar a las 8 AM

---

#### #F03-20 — Verificación final de FASE 03
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Stock calculado por movimientos (no por campo)
- [ ] Stock no puede ser negativo (constraint activo)
- [ ] Compra recibida → InventoryMovement creado → stock aumenta
- [ ] Concurrencia: 5 requests simultáneos con stock=3 → exactamente 3 exitosos
- [ ] Kardex muestra historial completo con saldo correcto
- [ ] Ajustes requieren autorización de OWNER y quedan auditados
- [ ] SALES y TECHNICIAN no pueden ver costos
- [ ] Alertas de stock bajo funcionan
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §9 Inventario, §10 Compras y Proveedores*
*Fase anterior: [FASE 02](FASE-02-catalogo.md) | Siguiente fase: [FASE 04](FASE-04-caja-pos-ventas.md)*
