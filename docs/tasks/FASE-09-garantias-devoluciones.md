# FASE 09 — Garantías y Devoluciones

**Rama:** `feature/fase-09-garantias`
**Objetivo:** Gestión centralizada de garantías (producto, reparación, instalación) con alertas automáticas. Flujo completo de devoluciones que nunca borra registros históricos.
**Prerrequisito:** FASE 08 completada y mergeada a `develop`.
**Criterio de salida:** Garantías creadas automáticamente en eventos de entrega. Devolución genera movimientos inversos sin eliminar venta original. Alertas de vencimiento funcionan.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 18 | 0% |

---

## Issues

### GARANTÍAS

---

#### #F09-01 — Modelo Warranty con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-08 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/warranties/domain/models.py`:
  ```
  Warranty:
    id (UUID, PK)
    code (VARCHAR, unique)            — GAR-YYYYMMDD-XXXXX
    customer_id (UUID, FK → Customer)
    source_type (ENUM): PRODUCT/REPAIR/INSTALLATION
    source_id (UUID)                  — ID del origen (polimórfico)
    product_id (UUID, FK → Product, nullable)
    serialized_unit_id (UUID, FK → SerializedUnit, nullable)
    start_date (DATE, not null)
    end_date (DATE, not null)
    duration_days (INTEGER, not null)
    status (ENUM): ACTIVE/EXPIRED/CLAIMED/VOID
    terms (TEXT)                      — condiciones de garantía
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

    INDEX: (customer_id, status)
    INDEX: (end_date) WHERE status = 'ACTIVE'   — para alertas
    INDEX: (code)                                — búsqueda rápida

  WarrantyClaim:
    id (UUID, PK)
    warranty_id (UUID, FK → Warranty)
    customer_id (UUID, FK → Customer)
    description (TEXT, not null)
    resolution (TEXT)
    status (ENUM): PENDING/IN_REVIEW/RESOLVED/REJECTED
    repair_order_id (UUID, FK → RepairOrder, nullable)  — si deriva en reparación
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic

---

#### #F09-02 — Creación automática de garantías en eventos de entrega
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-01

**Descripción:**
Las garantías se crean automáticamente. No es opcional. Verifica que las llamadas a `WarrantyService.create_from_*` ya existan en FASE 04, 07 y 08.

**Tareas:**
- [ ] Crear `WarrantyService`:
  - `create_from_sale(sale_id, product_id, user)` — al vender producto con garantía
  - `create_from_repair(repair_id, user)` — al entregar reparación (FASE 07 ya llama esto)
  - `create_from_installation(installation_id, user)` — al completar instalación
- [ ] Duración de garantía según fuente:
  - Producto: configurable por producto (campo `warranty_days` en Product, si no tiene → sin garantía)
  - Reparación: `settings.repair_warranty_days` (default 30)
  - Instalación: `settings.installation_warranty_days` (default 90)
- [ ] Crear un `Warranty` por cada producto serializado vendido
- [ ] Código autogenerado: `GAR-{YYYYMMDD}-{XXXXX}` transaccional
- [ ] Verificar que en FASE 04 se llama `create_from_sale` al completar venta
- [ ] Verificar que en FASE 07 se llama `create_from_repair` al entregar reparación
- [ ] Verificar que en FASE 08 se llama `create_from_installation` al completar instalación

**Definición de terminado:**
- [ ] Venta completada → Warranty creada automáticamente para productos con warranty_days
- [ ] Reparación entregada → Warranty creada (FASE 07 ya implementado, verificar)
- [ ] Instalación completada → Warranty creada

---

#### #F09-03 — Búsqueda y consulta de garantías
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-01

**Tareas:**
- [ ] Endpoints:
  - `GET /api/v1/warranties` — lista con filtros (admin)
  - `GET /api/v1/warranties/{id}` — detalle
  - `GET /api/v1/warranties/search` — búsqueda múltiple:
    - `?code=GAR-...`
    - `?customer_dni=...`
    - `?serial_number=...`
    - `?sale_code=VTA-...`
    - `?repair_code=REP-...`
  - `GET /api/v1/warranties/customer/{customer_id}` — garantías de un cliente
  - `GET /api/v1/warranties/{code}/public` — consulta pública por código (sin login)
- [ ] Respuesta pública: estado, fechas, producto, si está vigente (sin datos financieros)

---

#### #F09-04 — Reclamo de garantía (WarrantyClaim)
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-01

**Tareas:**
- [ ] `create_warranty_claim(warranty_id, description, user)`:
  - Verificar que Warranty.status = ACTIVE y end_date >= hoy
  - Crear WarrantyClaim(PENDING)
  - Warranty.status → CLAIMED
  - Notificación a OWNER
- [ ] `resolve_claim(claim_id, resolution, repair_order_id, user)`:
  - WarrantyClaim.status = RESOLVED
  - Si genera reparación: vincular RepairOrder
- [ ] `reject_claim(claim_id, reason, user)` (solo OWNER):
  - WarrantyClaim.status = REJECTED
  - Warranty.status → ACTIVE (puede seguir usándose)
- [ ] Endpoints:
  - `POST /api/v1/warranties/{id}/claims` — crear reclamo
  - `GET /api/v1/warranties/{id}/claims` — historial de reclamos
  - `PUT /api/v1/warranty-claims/{id}/resolve`
  - `PUT /api/v1/warranty-claims/{id}/reject`

---

#### #F09-05 — Tarea Celery: alertas de garantías próximas a vencer
- **Tipo:** `[TASK]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-01

**Tareas:**
- [ ] Tarea `check_expiring_warranties()`:
  - Garantías que vencen en 7 días → WhatsApp WARRANTY_EXPIRING al cliente + Notification a OWNER
  - Garantías que vencen en 30 días → Notification interna a OWNER solamente
  - Idempotente: no duplica alertas del mismo día
- [ ] Tarea `expire_warranties()`:
  - Garantías con `end_date < hoy` y `status = ACTIVE` → status = EXPIRED
- [ ] Ambas tareas en Beat: diariamente a las 7 AM

---

#### #F09-06 — Frontend de garantías (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-03

**Tareas:**
- [ ] `apps/web/app/admin/garantias/page.tsx`:
  - Lista con filtros: estado, tipo, fecha de vencimiento, cliente
  - Badge de urgencia: rojo si vence en ≤7 días, amarillo si ≤30 días, verde si activa
- [ ] `apps/web/app/admin/garantias/[id]/page.tsx`:
  - Detalle con fechas, producto/reparación/instalación de origen
  - Historial de reclamos
  - Botón de crear reclamo
- [ ] `apps/web/app/(public)/garantia/[code]/page.tsx` — consulta pública:
  - Formulario: código + DNI o teléfono de verificación
  - Resultado: estado, vigencia, qué cubre (sin datos internos)

---

#### #F09-07 — Portal del cliente: mis garantías
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-03

**Tareas:**
- [ ] `apps/web/app/customer/garantias/page.tsx`
- [ ] Lista de garantías activas y vencidas
- [ ] Detalle con fechas y qué cubre
- [ ] Botón de reclamar garantía (si está activa)

---

### DEVOLUCIONES

---

#### #F09-08 — Modelos Return y ReturnItem (completar desde FASE 04)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-01

**Descripción:**
Los modelos se crearon en FASE 04. Aquí se implementa el flujo completo.

**Tareas:**
- [ ] Verificar que `Return` y `ReturnItem` existen con la estructura:
  ```
  Return:
    id (UUID, PK)
    code (VARCHAR, unique)            — DEV-YYYY-XXXXX
    sale_id (UUID, FK → Sale)
    customer_id (UUID, FK → Customer)
    reason (ENUM):
      WITHIN_24_HOURS/WARRANTY/CREDIT_CANCELLATION/OTHER_AUTHORIZED
    status (ENUM): PENDING/APPROVED/COMPLETED/REJECTED
    total_refund (NUMERIC(14,2))
    notes (TEXT)
    authorized_by (UUID, FK → User)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

  ReturnItem:
    id (UUID, PK)
    return_id (UUID, FK → Return)
    sale_item_id (UUID, FK → SaleItem)
    product_id (UUID, FK → Product)
    serialized_unit_id (UUID, FK → SerializedUnit, nullable)
    quantity (NUMERIC(14,3))
    unit_price (NUMERIC(14,2))
    condition (ENUM): GOOD/DAMAGED/MISSING_PARTS
    refund_amount (NUMERIC(14,2))
    notes (TEXT)
  ```
- [ ] Si no existen: crear migración ahora

---

#### #F09-09 — Flujo completo de devolución
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-08

**Descripción:**
Una devolución nunca borra la venta. Genera movimientos inversos y ajustes de caja.

**Tareas:**
- [ ] Implementar `create_return(sale_id, items, reason, user)`:
  - Verificar que la venta existe y está en estado válido (PAID o COMPLETED)
  - Para `WITHIN_24_HOURS`: verificar que `sale.created_at >= now() - 24h`
  - Para `WARRANTY`: verificar que existe Warranty activa para el producto
  - Para `OTHER_AUTHORIZED`: solo OWNER puede iniciar
  - Crear Return(PENDING)
  - Solo OWNER puede aprobar devoluciones
- [ ] Implementar `approve_return(return_id, user)` (solo OWNER):
  ```
  [TRANSACCIÓN ATÓMICA]:
  1. Return.status = APPROVED
  2. Para cada ReturnItem:
     - InventoryMovement(RETURN, +qty) si condición es GOOD
     - InventoryMovement(DAMAGED, noop) si condición es DAMAGED
     - Si serializado: SerializedUnit.status = RETURNED (si GOOD) o DAMAGED
  3. CashMovement(EXPENSE, -refund_amount) si hay reembolso en efectivo
  4. Return.status = COMPLETED
  5. Sale.status = RETURNED (si es devolución total) o mantener (si es parcial)
  6. AuditLog: APPROVE_RETURN
  NUNCA eliminar la venta original
  ```
- [ ] Endpoints:
  - `POST /api/v1/returns` — solicitar devolución
  - `GET /api/v1/returns` — lista (admin)
  - `GET /api/v1/returns/{id}` — detalle
  - `POST /api/v1/returns/{id}/approve` — aprobar (solo OWNER)
  - `POST /api/v1/returns/{id}/reject` — rechazar (solo OWNER)

**Definición de terminado:**
- [ ] Devolución aprobada → InventoryMovement(RETURN) + CashMovement si aplica
- [ ] Venta original permanece en BD con status=RETURNED
- [ ] Serial devuelto → SerializedUnit.status = RETURNED
- [ ] Si serial en buen estado → vuelve a AVAILABLE en el inventario

---

#### #F09-10 — Frontend de devoluciones
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-09

**Tareas:**
- [ ] `apps/web/app/admin/ventas/[id]/devolucion/page.tsx` — formulario de devolución desde el detalle de venta
- [ ] Selección de ítems a devolver (parcial o total)
- [ ] Condición de cada ítem (GOOD/DAMAGED/MISSING_PARTS)
- [ ] Motivo de devolución obligatorio
- [ ] Cálculo automático del monto a reembolsar
- [ ] `apps/web/app/admin/devoluciones/page.tsx` — lista de devoluciones con estado

---

### SEEDS Y TESTS

---

#### #F09-11 — Seeds de garantías y devoluciones ficticias
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-01, #F09-08

**Tareas:**
- [ ] Garantías ficticias creadas a partir de ventas del seed anterior
- [ ] 1 garantía próxima a vencer (en 5 días)
- [ ] 1 garantía reclamada (CLAIMED)
- [ ] 1 devolución aprobada con movimientos de inventario correctos

---

#### #F09-12 — Tests de garantías
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-02, #F09-05

**Tareas:**
- [ ] `test_warranty_created_automatically_on_sale` — venta → Warranty creada
- [ ] `test_warranty_created_automatically_on_repair_delivery` — Warranty creada al entregar
- [ ] `test_warranty_created_automatically_on_installation_complete`
- [ ] `test_warranty_expiry_task_runs_idempotently`
- [ ] `test_expiring_warranty_alert_sent_to_customer`
- [ ] `test_expired_warranty_claim_rejected` → error
- [ ] `test_warranty_search_by_code`
- [ ] `test_warranty_public_query_no_sensitive_data` — respuesta pública sin datos financieros

---

#### #F09-13 — Tests de devoluciones
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-09

**Tareas:**
- [ ] `test_return_within_24h_success`
- [ ] `test_return_after_24h_requires_authorization` → error sin OWNER
- [ ] `test_return_restores_stock` — InventoryMovement(RETURN) creado
- [ ] `test_return_serial_unit_status_updated`
- [ ] `test_return_does_not_delete_sale` — Sale existe con status=RETURNED
- [ ] `test_return_creates_cash_movement_for_refund`
- [ ] `test_return_damaged_item_no_stock_restore`
- [ ] `test_sales_cannot_approve_return` → 403

---

#### #F09-14 — Integrar campo warranty_days en producto (FASE 02 update)
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-02

**Tareas:**
- [ ] Agregar campo `warranty_days (INTEGER, nullable)` al modelo Product
- [ ] Migración Alembic (additive, no rompe datos existentes)
- [ ] En el formulario de producto (FASE 02 frontend): agregar campo de días de garantía
- [ ] Si `warranty_days = NULL` o `0`: no generar Warranty al vender

---

#### #F09-15 — Documentar garantías y devoluciones
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar los motivos de devolución y sus condiciones en `docs/business-rules.md`
- [ ] Documentar cuándo se crea una garantía automáticamente
- [ ] Documentar el flujo de reclamo de garantía
- [ ] Documentar la política: nunca eliminar ventas, solo anular con motivo

---

### VERIFICACIÓN FINAL

---

#### #F09-16 — Búsqueda global: garantías y devoluciones
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-03

**Tareas:**
- [ ] Incluir garantías (por código GAR-...) en el módulo de búsqueda global
- [ ] Incluir devoluciones (por código DEV-...) en la búsqueda global
- [ ] Test: buscar `GAR-2026-00001` → retorna la garantía directamente

---

#### #F09-17 — Integrar garantías con módulo de clientes
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F09-03

**Tareas:**
- [ ] En el perfil del cliente (admin): agregar sección "Garantías activas"
- [ ] En el portal del cliente: sección visible de garantías vigentes
- [ ] Endpoint: `GET /api/v1/customers/{id}/warranties` — garantías del cliente

---

#### #F09-18 — Verificación final de FASE 09
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Garantías creadas automáticamente en venta, reparación e instalación
- [ ] Alerta de vencimiento enviada 7 días antes (WhatsApp + Notificación)
- [ ] Garantías expiradas marcadas automáticamente por tarea Celery
- [ ] Búsqueda por código GAR-... funciona
- [ ] Consulta pública sin datos financieros
- [ ] Devolución aprobada genera InventoryMovement y CashMovement
- [ ] Venta original nunca eliminada → status=RETURNED
- [ ] Serial devuelto en buen estado → AVAILABLE en inventario
- [ ] SALES no puede aprobar devoluciones → 403
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §18 Garantías*
*Fase anterior: [FASE 08](FASE-08-mantenimientos-instalaciones-envios.md) | Siguiente fase: [FASE 10](FASE-10-sublimacion.md)*
