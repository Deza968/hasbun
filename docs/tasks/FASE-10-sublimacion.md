# FASE 10 — Sublimación y Personalización

**Rama:** `feature/fase-10-sublimacion`
**Objetivo:** Sistema de órdenes de personalización (tazas, polos, productos) con flujo de diseño, cotización, producción y entrega. Arquitectura preparada para editor gráfico futuro.
**Prerrequisito:** FASE 09 completada y mergeada a `develop`.
**Criterio de salida:** Flujo completo desde solicitud de cliente hasta entrega. Archivos de diseño versionados en S3. Sin editor gráfico complejo todavía (arquitectura preparada).

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 14 | 0% |

---

## Issues

### MODELOS

---

#### #F10-01 — Modelos de sublimación con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-09 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/sublimation/domain/models.py`:
  ```
  CustomizationOrder:
    id (UUID, PK)
    code (VARCHAR, unique)               — SUB-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    status (ENUM):
      DRAFT/QUOTED/ACCEPTED/IN_PRODUCTION/READY/DELIVERED/CANCELLED
    total (NUMERIC(14,2))
    notes (TEXT)
    delivery_type (ENUM): PICKUP/DELIVERY
    cash_session_id (UUID, FK → CashSession, nullable)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  CustomizationItem:
    id (UUID, PK)
    order_id (UUID, FK → CustomizationOrder)
    product_id (UUID, FK → Product)      — producto base (taza, polo, etc.)
    quantity (INTEGER, not null)
    unit_price (NUMERIC(14,2))
    customization_notes (TEXT)           — instrucciones de personalización
    created_at (TIMESTAMPTZ)

  DesignFile:
    id (UUID, PK)
    order_id (UUID, FK → CustomizationOrder)
    item_id (UUID, FK → CustomizationItem, nullable)
    file_id (UUID, FK → FileObject)
    version (INTEGER, default 1)
    is_approved (BOOLEAN, default False)
    approved_by (UUID, FK → User, nullable)
    notes (TEXT)                         — observaciones sobre el diseño
    uploaded_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

  ProductionStatus:
    id (UUID, PK)
    order_id (UUID, FK → CustomizationOrder)
    stage (VARCHAR)                      — PRINTING/PRESSING/QUALITY_CHECK/PACKAGING
    updated_by (UUID, FK → User)
    notes (TEXT)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic
- [ ] Preparar campo en Product: `is_customizable (BOOLEAN, default False)` — migración additive
- [ ] En el seed de productos: marcar tazas y productos de sublimación como `is_customizable=True`

---

### LÓGICA DE NEGOCIO

---

#### #F10-02 — Servicio de órdenes de personalización
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-01

**Tareas:**
- [ ] Crear `CustomizationService`:
  - `create_order(customer_id, items, notes, user)` → CustomizationOrder(DRAFT)
  - `upload_design(order_id, item_id, file, notes, user)`:
    - Crear FileObject via FileService (FASE 02)
    - Crear DesignFile(version=N, is_approved=False)
    - Si ya existe diseño anterior: incrementar version
  - `approve_design(design_file_id, user)` (solo OWNER o SALES):
    - DesignFile.is_approved = True
  - `quote_order(order_id, items_prices, user)`:
    - Calcular total
    - CustomizationOrder.status = QUOTED
  - `accept_quote(order_id, user_or_customer)`:
    - CustomizationOrder.status = ACCEPTED
  - `start_production(order_id, user)`:
    - CustomizationOrder.status = IN_PRODUCTION
    - Crear ProductionStatus inicial
  - `update_production_stage(order_id, stage, notes, user)`:
    - Crear ProductionStatus entry
  - `mark_ready(order_id, user)`:
    - CustomizationOrder.status = READY
    - WhatsApp al cliente
  - `deliver_order(order_id, payment_data, user)`:
    - CashMovement
    - CustomizationOrder.status = DELIVERED
- [ ] Máquina de estados con transiciones válidas
- [ ] Endpoints:
  - `GET /api/v1/customizations` — lista (admin)
  - `POST /api/v1/customizations` — crear
  - `GET /api/v1/customizations/{id}` — detalle con diseños y producción
  - `POST /api/v1/customizations/{id}/designs` — subir diseño
  - `POST /api/v1/customizations/{id}/designs/{design_id}/approve` — aprobar diseño
  - `POST /api/v1/customizations/{id}/quote` — cotizar
  - `POST /api/v1/customizations/{id}/accept` — aceptar cotización
  - `POST /api/v1/customizations/{id}/start-production` — iniciar producción
  - `POST /api/v1/customizations/{id}/production-stage` — actualizar etapa
  - `POST /api/v1/customizations/{id}/ready` — marcar listo
  - `POST /api/v1/customizations/{id}/deliver` — entregar y cobrar

---

#### #F10-03 — Versionado de diseños
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Descripción:**
Cada versión del diseño se almacena. El historial no se borra.

**Tareas:**
- [ ] Endpoint: `GET /api/v1/customizations/{id}/designs` — lista de versiones por ítem
- [ ] Endpoint: `GET /api/v1/customizations/{id}/designs/{design_id}/url` — URL firmada del diseño
- [ ] Al subir nueva versión: la anterior no se elimina, solo se agrega con version+1
- [ ] Solo la última versión aprobada se usa para producción
- [ ] El cliente puede subir diseños desde su portal

---

### FRONTEND

---

#### #F10-04 — Vista de órdenes de sublimación (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Tareas:**
- [ ] `apps/web/app/admin/sublimacion/page.tsx`
- [ ] Tabla con: código, cliente, estado, items, total, fecha
- [ ] Filtros: estado, fecha
- [ ] `apps/web/app/admin/sublimacion/nueva/page.tsx`:
  - Selección de cliente
  - Selección de productos personalizables (`is_customizable=True`)
  - Cantidad y notas de personalización por ítem
  - Upload de diseño inicial (opcional)
- [ ] `apps/web/app/admin/sublimacion/[id]/page.tsx`:
  - Detalle completo con timeline de estados
  - Galería de versiones de diseño con botón de aprobar
  - Seguimiento de etapas de producción (PRINTING → PRESSING → etc.)
  - Botones de acción según estado

---

#### #F10-05 — Portal del cliente: solicitar personalización
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Tareas:**
- [ ] `apps/web/app/customer/sublimacion/page.tsx` — mis pedidos de personalización
- [ ] `apps/web/app/customer/sublimacion/nueva/page.tsx`:
  - Selección de producto
  - Instrucciones de personalización
  - Upload del diseño (JPG, PNG, PDF)
  - Notas adicionales
- [ ] Al enviar: orden en estado DRAFT, notificación al OWNER
- [ ] Vista del estado del pedido con timeline

---

#### #F10-06 — Tienda pública: productos personalizables
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-04

**Tareas:**
- [ ] En la tienda pública, los productos con `is_customizable=True` muestran botón "Personalizar"
- [ ] Click en "Personalizar" → si tiene cuenta: abrir formulario de solicitud
- [ ] Si no tiene cuenta: redirigir a registro o WhatsApp
- [ ] Preparar arquitectura para editor gráfico futuro (documentar punto de extensión)

---

### SEEDS Y TESTS

---

#### #F10-07 — Seeds de órdenes de sublimación ficticias
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Tareas:**
- [ ] 2 órdenes ficticias: 1 IN_PRODUCTION, 1 DELIVERED
- [ ] Diseños con versiones ficticias (archivos de prueba en MinIO)
- [ ] Marcar 3-5 productos del seed como `is_customizable=True`

---

#### #F10-08 — Tests de sublimación
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Tareas:**
- [ ] `test_create_customization_order`
- [ ] `test_upload_design_creates_version`
- [ ] `test_upload_second_design_increments_version`
- [ ] `test_production_requires_approved_design` → error si no hay diseño aprobado
- [ ] `test_deliver_creates_cash_movement`
- [ ] `test_invalid_state_transition` → error
- [ ] `test_design_history_immutable` — versiones anteriores no se eliminan

---

#### #F10-09 — WhatsApp en sublimación
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Tareas:**
- [ ] Al pasar a READY: WhatsApp al cliente ("tu pedido personalizado está listo")
- [ ] Al aceptar cotización: notificación interna al operador de producción

---

#### #F10-10 — Documentar módulo de sublimación
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar el flujo completo en `docs/business-rules.md`
- [ ] Documentar el punto de extensión para el editor gráfico futuro
- [ ] Documentar los formatos de archivo aceptados para diseños

---

### VERIFICACIÓN FINAL

---

#### #F10-11 — Integrar sublimación con módulo de clientes
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-02

**Tareas:**
- [ ] En el perfil del cliente (admin): sección "Órdenes de personalización"
- [ ] `GET /api/v1/customers/{id}/customizations`

---

#### #F10-12 — Preparar arquitectura para editor gráfico
- **Tipo:** `[DOCS]` `[BE]`
- **Prioridad:** 🟢 BAJO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-01

**Tareas:**
- [ ] Documentar en `docs/architecture.md` el punto de extensión:
  - Cómo el `DesignFile` se relacionará con un editor futuro
  - Qué campos adicionales necesitaría `CustomizationItem` (canvas data, layers, etc.)
  - Qué tecnología se recomienda (Fabric.js, Konva, etc.)
- [ ] Crear stub `apps/web/features/design-editor/` con README de extensión futura

---

#### #F10-13 — Seeds y verificación de producción
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F10-07

**Tareas:**
- [ ] Ejecutar seed completo → órdenes de sublimación ficticias correctas
- [ ] Verificar que los archivos de diseño ficticios existen en MinIO

---

#### #F10-14 — Verificación final de FASE 10
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Flujo completo DRAFT → DELIVERED funciona
- [ ] Diseños versionados (historial inmutable)
- [ ] Producción no inicia sin diseño aprobado
- [ ] Cliente puede subir diseño desde su portal
- [ ] WhatsApp al cliente cuando pedido está listo
- [ ] Productos marcados como personalizables visibles en tienda
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §20 Sublimación y Personalización*
*Fase anterior: [FASE 09](FASE-09-garantias-devoluciones.md) | Siguiente fase: [FASE 11](FASE-11-software-proyectos.md)*
