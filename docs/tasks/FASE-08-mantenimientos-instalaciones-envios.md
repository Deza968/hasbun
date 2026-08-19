# FASE 08 — Mantenimientos, Instalaciones y Envíos

**Rama:** `feature/fase-08-servicios`
**Objetivo:** Órdenes de mantenimiento, instalaciones de cámaras CCTV con evidencia obligatoria, solicitud de materiales con aprobación, y tracking de envíos de equipos por courier.
**Prerrequisito:** FASE 07 completada y mergeada a `develop`.
**Criterio de salida:** Instalación no puede marcarse COMPLETED sin fotos y documento firmado. Materiales no se consumen sin aprobación. Envíos con tracking vinculados a reparaciones.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 26 | 0% |

---

## Issues

### MANTENIMIENTOS

---

#### #F08-01 — Modelos de mantenimiento con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-07 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/maintenance/domain/models.py`:
  ```
  MaintenanceOrder:
    id (UUID, PK)
    code (VARCHAR, unique)              — MNT-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    type (ENUM):
      PREVENTIVE/CORRECTIVE/CLEANING/OPTIMIZATION/
      PRINTER_MAINTENANCE/COMPUTER_MAINTENANCE/LAPTOP_MAINTENANCE
    status (ENUM): PENDING/IN_PROGRESS/COMPLETED/CANCELLED
    device_type (VARCHAR)
    device_brand (VARCHAR)
    device_model (VARCHAR)
    device_serial (VARCHAR)
    technician_id (UUID, FK → User)
    scheduled_at (TIMESTAMPTZ)
    completed_at (TIMESTAMPTZ)
    cost (NUMERIC(14,2))
    description (TEXT)                  — trabajo realizado
    notes (TEXT)
    cash_session_id (UUID, FK → CashSession, nullable)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  MaintenancePartUsage:
    id (UUID, PK)
    maintenance_id (UUID, FK → MaintenanceOrder)
    product_id (UUID, FK → Product)
    quantity (NUMERIC(14,3))
    unit_cost (NUMERIC(14,2))
    status (ENUM): RESERVED/USED/RETURNED
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic

---

#### #F08-02 — Servicio de mantenimientos
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-01

**Tareas:**
- [ ] CRUD completo de MaintenanceOrder
- [ ] Consumo de inventario igual que reparaciones (reservar → usar → devolver)
- [ ] Cobro al completar → CashMovement
- [ ] Endpoints:
  - `GET /api/v1/maintenance` — lista con filtros (técnico, estado, tipo, fecha)
  - `POST /api/v1/maintenance` — crear
  - `GET /api/v1/maintenance/{id}` — detalle
  - `PUT /api/v1/maintenance/{id}` — actualizar
  - `POST /api/v1/maintenance/{id}/complete` — completar con descripción de trabajo
  - `POST /api/v1/maintenance/{id}/parts` — reservar material
  - `PUT /api/v1/maintenance/{id}/parts/{part_id}/use` — confirmar uso

---

#### #F08-03 — Frontend de mantenimientos
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-02

**Tareas:**
- [ ] `apps/web/app/admin/mantenimientos/page.tsx` — lista con filtros
- [ ] `apps/web/app/admin/mantenimientos/nuevo/page.tsx` — formulario de creación
- [ ] `apps/web/app/admin/mantenimientos/[id]/page.tsx` — detalle con materiales usados
- [ ] Vista móvil para técnico (igual que reparaciones)

---

### INSTALACIONES

---

#### #F08-04 — Modelos de instalación con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-07 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/installations/domain/models.py`:
  ```
  InstallationOrder:
    id (UUID, PK)
    code (VARCHAR, unique)              — INST-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    type (VARCHAR)                      — CCTV / RED / ELECTRICO / OTRO
    status (ENUM):
      QUOTED/ACCEPTED/SCHEDULED/IN_PROGRESS/WAITING_MATERIAL/COMPLETED/CANCELLED
    address (TEXT, not null)
    district, city (VARCHAR)
    coordinates_lat (NUMERIC(10,7))
    coordinates_lng (NUMERIC(10,7))
    technician_id (UUID, FK → User)
    total_cost (NUMERIC(14,2))
    notes (TEXT)
    cash_session_id (UUID, FK → CashSession, nullable)
    completed_at (TIMESTAMPTZ)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  InstallationCCTVDetail:              — detalles específicos de cámaras
    id (UUID, PK)
    installation_id (UUID, FK → InstallationOrder, unique)
    camera_count (INTEGER)
    camera_type (VARCHAR)              — analógica/IP/PTZ/domo
    dvr_nvr_model (VARCHAR)
    storage_capacity (VARCHAR)
    cable_type (VARCHAR)
    cable_meters (NUMERIC(8,2))
    power_source (VARCHAR)
    notes (TEXT)

  InstallationItem:                    — productos a instalar
    id (UUID, PK)
    installation_id (UUID, FK → InstallationOrder)
    product_id (UUID, FK → Product)
    quantity (NUMERIC(14,3))
    unit_price (NUMERIC(14,2))
    notes (TEXT)

  InstallationMaterial:                — materiales consumidos
    id (UUID, PK)
    installation_id (UUID, FK → InstallationOrder)
    product_id (UUID, FK → Product)
    quantity (NUMERIC(14,3))
    status (ENUM): REQUESTED/APPROVED/CONSUMED/RETURNED
    requested_by (UUID, FK → User)
    approved_by (UUID, FK → User)
    requested_at (TIMESTAMPTZ)
    approved_at (TIMESTAMPTZ)
    notes (TEXT)

  InstallationSchedule:
    id (UUID, PK)
    installation_id (UUID, FK → InstallationOrder)
    technician_id (UUID, FK → User)
    scheduled_date (DATE)
    scheduled_time (TIME)
    confirmed (BOOLEAN, default False)
    notes (TEXT)

  InstallationEvidence:
    id (UUID, PK)
    installation_id (UUID, FK → InstallationOrder)
    file_id (UUID, FK → FileObject)
    type (ENUM): BEFORE/DURING/AFTER/DOCUMENT_SIGNED
    description (TEXT)
    uploaded_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic para todas las tablas

---

#### #F08-05 — Flujo de estados de instalación
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-04

**Tareas:**
- [ ] Máquina de estados:
  ```
  QUOTED        → ACCEPTED (cliente acepta)
  ACCEPTED      → SCHEDULED (se agenda fecha y técnico)
  SCHEDULED     → IN_PROGRESS (técnico inicia en campo)
  IN_PROGRESS   → WAITING_MATERIAL (necesita materiales adicionales)
  IN_PROGRESS   → COMPLETED (todo listo)
  WAITING_MATERIAL → IN_PROGRESS (materiales aprobados y recibidos)
  * → CANCELLED
  ```
- [ ] Cada transición registra historial
- [ ] Al pasar a SCHEDULED: crear InstallationSchedule + notificación al técnico
- [ ] Al pasar a IN_PROGRESS: notificación a OWNER
- [ ] WhatsApp al cliente: INSTALLATION_CREATED al crear, INSTALLATION_UPCOMING 1 día antes

---

#### #F08-06 — Flujo de materiales adicionales (aprobación obligatoria)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05

**Descripción:**
El técnico NO puede consumir material sin aprobación. Flujo: solicitar → avisar cliente → avisar OWNER → aprobar → consumir.

**Tareas:**
- [ ] `request_additional_material(installation_id, product_id, quantity, reason, technician)`:
  - Crear InstallationMaterial(REQUESTED)
  - Notificación interna a OWNER
  - WhatsApp a cliente: "Se necesita material adicional para completar la instalación"
  - InstallationOrder.status → WAITING_MATERIAL
- [ ] `approve_material(material_id, owner_user)` (solo OWNER):
  - InstallationMaterial.status = APPROVED
  - InventoryMovement(ADJUSTMENT_OUT, -qty) del almacén
  - Notificación al técnico
- [ ] `confirm_material_consumed(material_id, technician)`:
  - InstallationMaterial.status = CONSUMED
  - InstallationOrder.status → IN_PROGRESS (si no hay más pendientes)
- [ ] El técnico NO puede marcar CONSUMED sin APPROVED previo → 400
- [ ] Endpoint:
  - `POST /api/v1/installations/{id}/materials` — solicitar
  - `PUT /api/v1/installations/{id}/materials/{mat_id}/approve` — aprobar (OWNER)
  - `PUT /api/v1/installations/{id}/materials/{mat_id}/consume` — confirmar consumo

**Definición de terminado:**
- [ ] Técnico solicita material → stock NO reducido todavía
- [ ] OWNER aprueba → stock reducido + técnico notificado
- [ ] Técnico confirma uso → material marcado CONSUMED
- [ ] Sin aprobación → CONSUMED no permitido

---

#### #F08-07 — Finalización de instalación (checklist obligatorio)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-06

**Descripción:**
No se puede marcar como COMPLETED sin cumplir todos los requisitos de cierre.

**Tareas:**
- [ ] Implementar `complete_installation(installation_id, completion_data, user)`:
  ```
  Verificaciones pre-completado (todas obligatorias):
  1. ¿Existe descripción del trabajo realizado? (campo no vacío)
  2. ¿Hay al menos 1 evidencia de tipo AFTER?
  3. ¿Hay al menos 1 InstallationEvidence de tipo DOCUMENT_SIGNED?
  4. ¿Están todos los materiales en CONSUMED o RETURNED?
  
  Si todo OK:
  [TRANSACCIÓN ATÓMICA]:
    - InstallationOrder.status = COMPLETED
    - InstallationOrder.completed_at = now()
    - CashMovement(INSTALLATION_PAYMENT, IN)
    - AuditLog: COMPLETE_INSTALLATION
  ```
- [ ] Si falta cualquier requisito → error con detalle de qué falta
- [ ] Endpoint: `POST /api/v1/installations/{id}/complete`

**Definición de terminado:**
- [ ] Sin foto AFTER → error indicando que falta
- [ ] Sin documento firmado → error indicando que falta
- [ ] Con todo completo → COMPLETED + CashMovement

---

#### #F08-08 — Frontend de instalaciones
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05

**Tareas:**
- [ ] `apps/web/app/admin/instalaciones/page.tsx` — lista con filtros y mapa opcional
- [ ] `apps/web/app/admin/instalaciones/nueva/page.tsx` — formulario:
  - Datos del cliente y dirección
  - Tipo de instalación (CCTV activa sub-formulario de detalles de cámara)
  - Productos a instalar
  - Fecha y técnico programado
- [ ] `apps/web/app/admin/instalaciones/[id]/page.tsx`:
  - Timeline de estados
  - Sección de materiales con estado de aprobación
  - Galería de evidencias clasificada por etapa (BEFORE/DURING/AFTER/DOCUMENT)
  - Checklist de completado (muestra qué falta)
  - Botón de completar (solo activo cuando checklist está 100%)
- [ ] Vista móvil para técnico: subir fotos, solicitar materiales, actualizar estado

---

#### #F08-09 — Calendario de instalaciones y mantenimientos
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-02, #F08-05

**Tareas:**
- [ ] `apps/web/app/admin/calendario/page.tsx`
- [ ] Vista mensual/semanal/diaria con eventos:
  - Instalaciones programadas
  - Mantenimientos programados
  - Reparaciones (fecha estimada de entrega)
- [ ] Filtro por técnico
- [ ] Color por tipo de evento
- [ ] Al hacer clic en evento: mini-detalle con enlace al detalle completo
- [ ] Preparar estructura para agregar más tipos de eventos en FASE 12

---

### ENVÍOS

---

#### #F08-10 — Modelo Shipment con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-07 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/shipping/domain/models.py`:
  ```
  Shipment:
    id (UUID, PK)
    code (VARCHAR, unique)              — ENV-YYYY-XXXXX
    repair_id (UUID, FK → RepairOrder, nullable)
    customer_id (UUID, FK → Customer)
    direction (ENUM): TO_HASBUN/FROM_HASBUN
    carrier (VARCHAR)
    tracking_number (VARCHAR)
    origin_address (TEXT)
    destination_address (TEXT)
    cost (NUMERIC(14,2))
    status (ENUM):
      PENDING/SHIPPED/IN_TRANSIT/RECEIVED/
      RETURN_SHIPPED/DELIVERED/LOST/CANCELLED
    sent_at (TIMESTAMPTZ)
    received_at (TIMESTAMPTZ)
    estimated_delivery (DATE)
    evidence_file_id (UUID, FK → FileObject, nullable)
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic

---

#### #F08-11 — Servicio y endpoints de envíos
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-10

**Tareas:**
- [ ] CRUD completo de Shipment
- [ ] Vincular con RepairOrder (una reparación puede tener 2 envíos: ida y vuelta)
- [ ] Al recibir envío `TO_HASBUN`: RepairOrder puede transicionar automáticamente
- [ ] Al despachar envío `FROM_HASBUN`: RepairOrder.status = DELIVERED
- [ ] Endpoints:
  - `GET /api/v1/shipments` — lista con filtros
  - `POST /api/v1/shipments` — crear
  - `GET /api/v1/shipments/{id}` — detalle
  - `PUT /api/v1/shipments/{id}/status` — actualizar estado con evidencia
  - `GET /api/v1/repairs/{id}/shipments` — envíos de una reparación

---

#### #F08-12 — Modelo DeliveryOrder con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-04 completa (Sale)

**Tareas:**
- [ ] Crear `apps/api/app/modules/deliveries/domain/models.py`:
  ```
  DeliveryOrder:
    id (UUID, PK)
    code (VARCHAR, unique)              — DEL-YYYY-XXXXX
    reference_type (VARCHAR)            — sale / repair / other
    reference_id (UUID)
    customer_id (UUID, FK → Customer)
    status (ENUM):
      PENDING/CONFIRMED/PREPARING/READY/IN_DELIVERY/DELIVERED/CANCELLED
    delivery_address (TEXT)
    district, city (VARCHAR)
    delivery_zone (VARCHAR)
    cost (NUMERIC(14,2))
    cost_type (ENUM): FIXED/ZONE/DISTANCE/COURIER/FREE
    carrier_name (VARCHAR)
    carrier_phone (VARCHAR)
    scheduled_at (TIMESTAMPTZ)
    delivered_at (TIMESTAMPTZ)
    notes (TEXT)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic

---

#### #F08-13 — Servicio y frontend de delivery
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-12

**Tareas:**
- [ ] CRUD completo de DeliveryOrder
- [ ] Vinculación con ventas y reparaciones
- [ ] Endpoints standard: GET lista, POST crear, PUT estado
- [ ] `apps/web/app/admin/delivery/page.tsx` — lista con estados y filtros
- [ ] `apps/web/app/admin/envios/page.tsx` — lista de Shipments
- [ ] Vista unificada de "logística" con tabs: Delivery local / Envíos courier

---

### TESTS

---

#### #F08-14 — Tests de instalaciones
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-07

**Tareas:**
- [ ] `test_cannot_complete_without_evidence_photo` → error descriptivo
- [ ] `test_cannot_complete_without_signed_document` → error descriptivo
- [ ] `test_technician_cannot_consume_unapproved_material` → 400
- [ ] `test_material_approval_reduces_stock`
- [ ] `test_complete_installation_creates_cash_movement`
- [ ] `test_complete_installation_atomically` — si falla CashMovement → no COMPLETED

---

#### #F08-15 — Tests de mantenimientos
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-02

**Tareas:**
- [ ] `test_complete_maintenance_with_parts`
- [ ] `test_part_reserved_reduces_available_stock`
- [ ] `test_cancelled_maintenance_returns_reserved_parts`

---

#### #F08-16 — Tests de envíos
- **Tipo:** `[TEST]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-11

**Tareas:**
- [ ] `test_shipment_linked_to_repair`
- [ ] `test_receive_shipment_updates_repair_status`
- [ ] `test_invalid_status_transition_shipment` → error

---

### SEEDS Y DOCUMENTACIÓN

---

#### #F08-17 — Seeds de instalaciones, mantenimientos y envíos
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-04, #F08-01

**Tareas:**
- [ ] 2 instalaciones ficticias: 1 SCHEDULED, 1 COMPLETED con evidencias
- [ ] 2 mantenimientos ficticios: 1 IN_PROGRESS, 1 COMPLETED
- [ ] 1 envío ficticio vinculado a reparación

---

#### #F08-18 — Tarea Celery: recordatorio de instalaciones próximas
- **Tipo:** `[TASK]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05

**Tareas:**
- [ ] Tarea `send_installation_reminders()`:
  - Instalaciones con `scheduled_date == mañana` → WhatsApp INSTALLATION_UPCOMING al cliente
  - Notificación interna al técnico asignado
- [ ] Configurar en Beat: diariamente a las 8 AM

---

#### #F08-19 — Documentar módulos de servicios
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar el flujo de materiales adicionales en instalaciones
- [ ] Documentar el checklist de completado de instalación
- [ ] Documentar los tipos de envío (TO_HASBUN / FROM_HASBUN)

---

### VERIFICACIÓN FINAL

---

#### #F08-20 — Seeds completos de fase 08
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-17

**Tareas:**
- [ ] Ejecutar seed completo → todos los módulos tienen datos ficticios coherentes

---

#### #F08-21 — Portal del cliente: mis instalaciones y envíos
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05, #F08-11

**Tareas:**
- [ ] `apps/web/app/customer/instalaciones/page.tsx` — lista de instalaciones del cliente
- [ ] `apps/web/app/customer/envios/page.tsx` — tracking de envíos con número de guía

---

#### #F08-22 — Integrar WhatsApp en instalaciones
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05, FASE-06 WhatsApp

**Tareas:**
- [ ] Al programar instalación → WhatsApp: INSTALLATION_CREATED
- [ ] 1 día antes → WhatsApp: INSTALLATION_UPCOMING
- [ ] Al completar → WhatsApp de confirmación al cliente

---

#### #F08-23 — Tests de WhatsApp en servicios
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-22

**Tareas:**
- [ ] `test_installation_reminder_sent_day_before`
- [ ] `test_material_request_notifies_owner`
- [ ] `test_material_request_notifies_customer`

---

#### #F08-24 — Foto antes de iniciar instalación (BEFORE obligatoria)
- **Tipo:** `[BE]` `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05

**Tareas:**
- [ ] Al transicionar a IN_PROGRESS: verificar que hay al menos 1 foto BEFORE
- [ ] Si no hay foto BEFORE → error con mensaje claro
- [ ] Frontend: recordatorio visual antes de marcar "Iniciar instalación"

---

#### #F08-25 — Tarea Celery: instalaciones sin completar (abandono)
- **Tipo:** `[TASK]`
- **Prioridad:** 🟢 BAJO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F08-05

**Tareas:**
- [ ] Tarea diaria: instalaciones en IN_PROGRESS por más de X días (configurable)
- [ ] Crear notificación de alerta para OWNER

---

#### #F08-26 — Verificación final de FASE 08
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Instalación no puede completarse sin foto AFTER y documento firmado
- [ ] Material adicional no se consume sin aprobación de OWNER
- [ ] WhatsApp enviado en eventos de instalación
- [ ] Mantenimientos consumen inventario via InventoryMovement
- [ ] Envíos vinculados a reparaciones funcionan
- [ ] Delivery local con estados correctos
- [ ] Calendario muestra instalaciones y mantenimientos
- [ ] Vista móvil del técnico funcional
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §16 Mantenimientos, §17 Instalaciones, §19 Delivery y Envíos*
*Fase anterior: [FASE 07](FASE-07-reparaciones.md) | Siguiente fase: [FASE 09](FASE-09-garantias-devoluciones.md)*
