# FASE 07 — Reparaciones

**Rama:** `feature/fase-07-reparaciones`
**Objetivo:** Sistema completo de órdenes de reparación con diagnóstico, cotización al cliente, control de repuestos, credenciales cifradas, evidencias y garantía automática al entregar.
**Prerrequisito:** FASE 06 completada y mergeada a `develop`.
**Criterio de salida:** Flujo completo de reparación funciona. Credenciales cifradas. Repuestos controlados por InventoryMovement. Garantía creada automáticamente al entregar.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 28 | 0% |

---

## Issues

### MODELOS

---

#### #F07-01 — Modelos principales de reparación con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-06 completa

**Tareas:**
- [ ] Crear `apps/api/app/modules/repairs/domain/models.py`:
  ```
  RepairOrder:
    id (UUID, PK)
    code (VARCHAR, unique)          — REP-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    technician_id (UUID, FK → User, nullable)
    status (ENUM):
      RECEIVED/DIAGNOSING/QUOTED/WAITING_CUSTOMER/AUTHORIZED/
      IN_REPAIR/TESTING/READY/DELIVERED/REJECTED/
      CANCELLED_BY_CUSTOMER/NOT_REPAIRABLE/ABANDONED
    authorized_limit (NUMERIC(14,2))  — tope autorizado por cliente
    total_cost (NUMERIC(14,2))        — costo final cobrado
    cash_session_id (UUID, FK → CashSession, nullable)
    notes (TEXT)
    received_at (TIMESTAMPTZ)
    delivered_at (TIMESTAMPTZ)
    estimated_ready_at (TIMESTAMPTZ)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  RepairDevice:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder, unique)
    type (VARCHAR)                  — laptop/computadora/impresora/otro
    brand (VARCHAR)
    model (VARCHAR)
    serial_number (VARCHAR)
    imei, imei2 (VARCHAR)
    accessories (TEXT)              — lista separada por comas o JSON
    physical_condition (TEXT)
    reported_problem (TEXT, not null)
    observations (TEXT)             — notas del técnico al recibir

  RepairStatusHistory:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    old_status (VARCHAR)
    new_status (VARCHAR, not null)
    changed_by (UUID, FK → User)
    note (TEXT)
    changed_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic para estas tablas

---

#### #F07-02 — Modelos de diagnóstico, cotización y autorización
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-01

**Tareas:**
- [ ] Crear modelos:
  ```
  RepairDiagnosis:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    technician_id (UUID, FK → User)
    description (TEXT, not null)
    authorized_limit (NUMERIC(14,2))  — tope propuesto por técnico
    created_at (TIMESTAMPTZ)
    updated_at (TIMESTAMPTZ)

  RepairQuote:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    parts_cost (NUMERIC(14,2))
    labor_cost (NUMERIC(14,2))
    total (NUMERIC(14,2))             — parts_cost + labor_cost
    authorized_limit (NUMERIC(14,2))
    status (ENUM): PENDING/ACCEPTED/REJECTED
    sent_via_whatsapp (BOOLEAN, default False)
    customer_response_at (TIMESTAMPTZ)
    rejection_reason (TEXT)
    created_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

  RepairAuthorization:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    type (ENUM): INITIAL_REPAIR/COST_EXCEEDED/ADDITIONAL_PARTS
    requested_limit (NUMERIC(14,2))
    approved_limit (NUMERIC(14,2))
    status (ENUM): PENDING/APPROVED/REJECTED
    requested_by (UUID, FK → User)
    channel (VARCHAR)               — whatsapp / presencial / telefono
    response_at (TIMESTAMPTZ)
    notes (TEXT)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic

---

#### #F07-03 — Modelos de repuestos, evidencias y garantía de reparación
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-01

**Tareas:**
- [ ] Crear modelos:
  ```
  RepairPartUsage:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    product_id (UUID, FK → Product)
    quantity (NUMERIC(14,3))
    unit_cost (NUMERIC(14,2))
    status (ENUM): RESERVED/USED/RETURNED/DAMAGED
    reserved_at (TIMESTAMPTZ)
    used_at (TIMESTAMPTZ)
    returned_at (TIMESTAMPTZ)
    notes (TEXT)

  RepairEvidence:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    file_id (UUID, FK → FileObject)
    stage (ENUM): RECEPTION/DIAGNOSIS/IN_PROGRESS/COMPLETED
    description (TEXT)
    uploaded_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)

  RepairWarranty:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder, unique)
    warranty_id (UUID, FK → Warranty)
    duration_days (INTEGER)
    terms (TEXT)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración Alembic

---

#### #F07-04 — Modelo de credenciales de acceso (cifradas)
- **Tipo:** `[BE]` `[DB]` `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-01

**Tareas:**
- [ ] Crear modelo:
  ```
  RepairAccessCredential:
    id (UUID, PK)
    repair_id (UUID, FK → RepairOrder)
    method (ENUM):
      PASSWORD/PIN/PATTERN/WINDOWS_PASSWORD/BIOS_PASSWORD/OTHER
    value_encrypted (TEXT, not null)   — AES-256-GCM
    other_description (VARCHAR)        — si method = OTHER
    last_accessed_at (TIMESTAMPTZ)
    last_accessed_by (UUID, FK → User)
    created_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] Implementar `CredentialEncryptionService`:
  - `encrypt(plain_text) -> str` — AES-256-GCM con clave de settings
  - `decrypt(cipher_text) -> str` — solo para usuarios autorizados
  - La clave de cifrado viene de `settings.CREDENTIAL_ENCRYPTION_KEY` (variable de entorno)
  - Nunca loguear el valor descifrado
- [ ] El valor se cifra antes de guardar en BD, nunca en texto plano
- [ ] Cada lectura (decrypt) genera AuditLog: `ACCESS_REPAIR_CREDENTIALS`

**Definición de terminado:**
- [ ] Credencial guardada → solo texto cifrado en BD
- [ ] Solo técnico asignado y OWNER pueden descifrar
- [ ] Cada lectura queda en AuditLog
- [ ] SALES intenta ver credencial → 403

---

### LÓGICA DE NEGOCIO

---

#### #F07-05 — Generador de código REP y servicio base
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-01

**Tareas:**
- [ ] Código usando `generate_document_code("REP", session)` de FASE 04 → `REP-2026-00001`
- [ ] Crear `RepairService` con método `create_repair_order(customer_id, device_data, created_by)`:
  - Crear RepairOrder(RECEIVED)
  - Crear RepairDevice
  - Crear RepairStatusHistory (None → RECEIVED)
  - AuditLog: CREATE_REPAIR
- [ ] Cada cambio de estado crea RepairStatusHistory automáticamente

---

#### #F07-06 — Flujo de estados de reparación
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-05

**Descripción:**
Cada transición de estado debe ser explícita y validada. No se puede saltar estados arbitrariamente.

**Tareas:**
- [ ] Implementar máquina de estados con transiciones válidas:
  ```
  RECEIVED       → DIAGNOSING (técnico asignado)
  DIAGNOSING     → QUOTED (diagnóstico completado + cotización creada)
  QUOTED         → WAITING_CUSTOMER (cotización enviada al cliente)
  WAITING_CUSTOMER → AUTHORIZED (cliente acepta)
  WAITING_CUSTOMER → REJECTED (cliente rechaza)
  AUTHORIZED     → IN_REPAIR (técnico inicia reparación)
  IN_REPAIR      → TESTING (trabajo físico completado)
  IN_REPAIR      → WAITING_CUSTOMER (costo supera límite autorizado)
  TESTING        → READY (equipo pasa pruebas)
  READY          → DELIVERED (cliente recoge y paga)
  * → CANCELLED_BY_CUSTOMER (cliente cancela en cualquier momento)
  * → NOT_REPAIRABLE (técnico determina irreparable)
  * → ABANDONED (no recogido en X días, configurable)
  ```
- [ ] Transición inválida → `BusinessRuleError("INVALID_STATUS_TRANSITION")`
- [ ] Cada transición registra `RepairStatusHistory`
- [ ] Cada transición dispara evento WhatsApp si corresponde

---

#### #F07-07 — Diagnóstico y cotización al cliente
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-06

**Tareas:**
- [ ] `diagnose_repair(repair_id, description, authorized_limit, technician)`:
  - Crear RepairDiagnosis
  - Estado permanece en DIAGNOSING hasta crear cotización
- [ ] `create_repair_quote(repair_id, parts_cost, labor_cost, technician)`:
  - Crear RepairQuote
  - RepairOrder.status → QUOTED → WAITING_CUSTOMER (automático al enviar por WhatsApp)
  - Dispara WhatsApp: QUOTE_CREATED al cliente
- [ ] `respond_repair_quote(quote_id, accepted, rejection_reason)`:
  - Si accepted: RepairQuote.status = ACCEPTED, RepairOrder.status = AUTHORIZED
    - Crear RepairAuthorization
    - Dispara WhatsApp: QUOTE_ACCEPTED a OWNER + SALES
  - Si rejected: RepairQuote.status = REJECTED, RepairOrder.status = REJECTED
- [ ] **Regla:** No iniciar reparación sin autorización del cliente
- [ ] Endpoints:
  - `POST /api/v1/repairs/{id}/diagnose`
  - `POST /api/v1/repairs/{id}/quote`
  - `POST /api/v1/repairs/{id}/respond-quote`

---

#### #F07-08 — Control del tope de reparación
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-07

**Descripción:**
Si el costo supera el límite autorizado, la reparación se pausa y requiere nueva autorización del cliente.

**Tareas:**
- [ ] Implementar verificación de tope en `update_repair_costs(repair_id, parts_cost, labor_cost, technician)`:
  ```
  current_total = parts_cost + labor_cost + used_parts_cost
  
  SI current_total <= repair_order.authorized_limit:
    → continuar normalmente
  
  SI current_total > repair_order.authorized_limit:
    → RepairOrder.status = WAITING_CUSTOMER
    → Crear RepairAuthorization(PENDING, type=COST_EXCEEDED)
    → WhatsApp al cliente: "El costo supera el límite acordado. Nuevo total: S/{total}. ¿Autoriza continuar?"
    → Notificación interna a OWNER
  ```
- [ ] `approve_cost_exceeded(authorization_id, new_limit, user)`:
  - Actualizar RepairOrder.authorized_limit
  - RepairOrder.status → IN_REPAIR
- [ ] Endpoint: `POST /api/v1/repairs/{id}/authorize-cost`

---

#### #F07-09 — Gestión de repuestos con inventario
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-03, #F03-03

**Descripción:**
El técnico no consume stock directamente. El flujo es: solicitar → usar → devolver si no se usa.

**Tareas:**
- [ ] `reserve_repair_part(repair_id, product_id, quantity, technician)`:
  - Verificar stock disponible
  - Crear RepairPartUsage(RESERVED)
  - InventoryMovement(REPAIR_USAGE, -qty) — preliminar como reserva
  - AuditLog
- [ ] `confirm_part_used(part_usage_id, technician)`:
  - RepairPartUsage.status = USED
  - used_at = now()
- [ ] `return_unused_part(part_usage_id, technician)`:
  - RepairPartUsage.status = RETURNED
  - InventoryMovement(REPAIR_RETURN, +qty)
- [ ] Al cancelar reparación: todos los RESERVED → RETURNED automáticamente
- [ ] Endpoints:
  - `POST /api/v1/repairs/{id}/parts` — reservar repuesto
  - `PUT /api/v1/repairs/{id}/parts/{part_id}/use` — confirmar uso
  - `PUT /api/v1/repairs/{id}/parts/{part_id}/return` — devolver

**Definición de terminado:**
- [ ] Reservar repuesto reduce stock disponible
- [ ] Devolver repuesto restaura stock
- [ ] Cancelar reparación devuelve todos los repuestos RESERVED al inventario

---

#### #F07-10 — Entrega de reparación y cobro
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-06, #F07-03

**Descripción:**
No se puede entregar sin registrar el cobro. La entrega genera garantía automáticamente.

**Tareas:**
- [ ] Implementar `deliver_repair(repair_id, payment_data, user)`:
  ```
  [TRANSACCIÓN ATÓMICA]:
  1. Verificar status = READY
  2. Verificar que existe pago registrado (o registrarlo ahora)
  3. CashMovement(REPAIR_PAYMENT, IN) en sesión activa
  4. RepairOrder.status = DELIVERED
  5. RepairOrder.delivered_at = now()
  6. Crear RepairWarranty + Warranty (automático, no opcional)
  7. AuditLog: DELIVER_REPAIR
  SI CashMovement falla → ROLLBACK (equipo no entregado)
  ```
- [ ] WhatsApp: REPAIR_READY (al pasar a READY), mensaje de entrega al pasar a DELIVERED
- [ ] Endpoint: `POST /api/v1/repairs/{id}/deliver`

**Definición de terminado:**
- [ ] No se puede entregar sin CashMovement previo → error
- [ ] Entrega exitosa → Warranty creada automáticamente
- [ ] Si falla el cobro → ROLLBACK (status no cambia)

---

#### #F07-11 — Cancelación de reparación
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-09

**Tareas:**
- [ ] Implementar `cancel_repair(repair_id, reason, user)`:
  ```
  [TRANSACCIÓN ATÓMICA]:
  1. RepairOrder.status = CANCELLED_BY_CUSTOMER
  2. Para cada RepairPartUsage con status=RESERVED:
     - InventoryMovement(REPAIR_RETURN, +qty)
     - RepairPartUsage.status = RETURNED
  3. Para cada RepairPartUsage con status=USED:
     - Mantener en USED (se cobran si el cliente autorizó)
  4. Si NO hay partes USED y NO hay labor: no cobrar diagnóstico
  5. Si hay partes USED: calcular cobro según autorización
  6. AuditLog: CANCEL_REPAIR
  ```
- [ ] Endpoint: `POST /api/v1/repairs/{id}/cancel`

---

### EVIDENCIAS Y ARCHIVOS

---

#### #F07-12 — Upload de evidencias fotográficas
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-03, FASE-02 FileObject

**Tareas:**
- [ ] Endpoint: `POST /api/v1/repairs/{id}/evidence` — subir foto (multipart)
  - El técnico sube desde móvil
  - Se comprime si > 2MB (lógica en frontend)
  - `stage`: RECEPTION / DIAGNOSIS / IN_PROGRESS / COMPLETED
  - Crear FileObject + RepairEvidence
- [ ] `GET /api/v1/repairs/{id}/evidence` — listar fotos por etapa
- [ ] Mínimo 1 foto obligatoria al pasar a READY

---

### FRONTEND

---

#### #F07-13 — Lista y búsqueda de reparaciones (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-05

**Tareas:**
- [ ] `apps/web/app/admin/reparaciones/page.tsx`
- [ ] Tabla con: código, cliente, dispositivo, técnico, estado, fecha entrada, fecha estimada
- [ ] Filtros: estado, técnico, tipo de dispositivo, fecha
- [ ] Badge de estado con colores (READY en verde brillante, ABANDONED en gris, etc.)
- [ ] Búsqueda rápida por código REP-... (búsqueda global)
- [ ] Botón "Nueva reparación"

---

#### #F07-14 — Formulario de nueva reparación
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-05

**Tareas:**
- [ ] `apps/web/app/admin/reparaciones/nueva/page.tsx`
- [ ] Sección 1: Selección/creación de cliente
- [ ] Sección 2: Datos del dispositivo (tipo, marca, modelo, serial, accesorios)
- [ ] Sección 3: Condición física y problema reportado
- [ ] Sección 4: Credenciales de acceso (opcional, campo de contraseña oculto)
- [ ] Foto de recepción (captura desde cámara o subida)
- [ ] Asignar técnico (si tiene permiso)

---

#### #F07-15 — Detalle de reparación (admin y técnico)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-06

**Tareas:**
- [ ] `apps/web/app/admin/reparaciones/[id]/page.tsx`
- [ ] Timeline visual de estados (paso a paso con timestamps)
- [ ] Información del dispositivo
- [ ] Sección de diagnóstico y cotización
- [ ] Lista de repuestos usados/reservados
- [ ] Galería de evidencias por etapa
- [ ] Acciones disponibles según estado actual (botones de transición)
- [ ] Sección de credenciales (botón "Ver contraseña" → confirmación → AuditLog automático)
- [ ] Sección de cobro y entrega

---

#### #F07-16 — Vista móvil del técnico (reparaciones)
- **Tipo:** `[FE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-15

**Descripción:**
El técnico opera principalmente desde su celular. La UI debe ser mobile-first y optimizada.

**Tareas:**
- [ ] Layout mobile-first para ruta `/admin/reparaciones/[id]` cuando el viewport es móvil
- [ ] Botones grandes y accesibles con el pulgar
- [ ] Subida de foto directa desde cámara del celular
- [ ] Cambio de estado con confirmación en un tap
- [ ] Formulario de diagnóstico optimizado para teclado móvil
- [ ] Sin tablas horizontales que requieran scroll lateral

---

#### #F07-17 — Consulta pública de reparación (sin login)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-05

**Tareas:**
- [ ] `apps/web/app/(public)/reparacion/[code]/page.tsx`
- [ ] El cliente ingresa: código REP-... + DNI o teléfono
- [ ] Muestra: estado actual, timeline simplificado, fecha estimada
- [ ] No muestra: costos, credenciales, información interna
- [ ] Endpoint público: `GET /api/v1/repairs/{code}/status?dni=...`

---

#### #F07-18 — Portal del cliente: mis reparaciones
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-05

**Tareas:**
- [ ] `apps/web/app/customer/reparaciones/page.tsx`
- [ ] Lista de reparaciones del cliente con estado actual
- [ ] Detalle con timeline (sin info financiera interna)
- [ ] Poder responder cotización (aceptar/rechazar) desde el portal

---

### SEEDS Y TESTS

---

#### #F07-19 — Seeds de reparaciones ficticias
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-05

**Tareas:**
- [ ] 1 reparación en RECEIVED (recién ingresada)
- [ ] 1 reparación en IN_REPAIR con repuestos reservados
- [ ] 1 reparación en READY (lista para entregar)
- [ ] 1 reparación DELIVERED con garantía creada
- [ ] 1 reparación CANCELLED_BY_CUSTOMER con repuestos devueltos

---

#### #F07-20 — Tests de flujo de reparación
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-06

**Tareas:**
- [ ] `test_repair_full_flow` — RECEIVED → DIAGNOSING → QUOTED → AUTHORIZED → IN_REPAIR → TESTING → READY → DELIVERED
- [ ] `test_invalid_state_transition` → error al saltar estados
- [ ] `test_status_history_recorded` — cada cambio de estado registrado
- [ ] `test_cannot_start_repair_without_authorization` → error
- [ ] `test_cost_exceeds_limit_pauses_repair` — superar tope → WAITING_CUSTOMER

---

#### #F07-21 — Tests de repuestos
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-09

**Tareas:**
- [ ] `test_reserve_part_reduces_available_stock`
- [ ] `test_return_unused_part_restores_stock`
- [ ] `test_cancel_repair_returns_all_reserved_parts`
- [ ] `test_used_parts_not_returned_on_cancel`
- [ ] `test_insufficient_stock_for_part` → error

---

#### #F07-22 — Tests de credenciales
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-04

**Tareas:**
- [ ] `test_credential_stored_encrypted` — BD no contiene texto plano
- [ ] `test_assigned_technician_can_view_credential`
- [ ] `test_other_technician_cannot_view_credential` → 403
- [ ] `test_view_credential_creates_audit_log`
- [ ] `test_credential_not_logged` — logs no contienen el valor descifrado

---

#### #F07-23 — Tests de entrega y cobro
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-10

**Tareas:**
- [ ] `test_deliver_creates_warranty_automatically`
- [ ] `test_cannot_deliver_without_payment` → error
- [ ] `test_deliver_payment_rollback_on_failure` — si falla CashMovement → status no cambia
- [ ] `test_repair_whatsapp_ready_notification` — WhatsApp enviado al pasar a READY

---

#### #F07-24 — Tests de cancelación
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-11

**Tareas:**
- [ ] `test_cancel_without_parts_no_charge`
- [ ] `test_cancel_with_used_parts_charges_correctly`
- [ ] `test_cancel_returns_reserved_parts_to_inventory`

---

### DOCUMENTACIÓN

---

#### #F07-25 — Documentar módulo de reparaciones
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar la máquina de estados en `docs/business-rules.md`
- [ ] Documentar el flujo de repuestos y relación con inventario
- [ ] Documentar el manejo de credenciales cifradas en `docs/security.md`
- [ ] Documentar la política de cancelación (con/sin repuestos usados)

---

#### #F07-26 — Integrar WhatsApp en reparaciones
- **Tipo:** `[BE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-06, FASE-06 WhatsApp

**Tareas:**
- [ ] Al crear orden → WhatsApp: REPAIR_CREATED (recibo al cliente)
- [ ] Al enviar cotización → WhatsApp: QUOTE_CREATED (cotización con total)
- [ ] Al pasar a READY → WhatsApp: REPAIR_READY ("tu equipo está listo")
- [ ] Al superar tope → WhatsApp solicitando nueva autorización

---

### VERIFICACIÓN FINAL

---

#### #F07-27 — Verificación del cifrado en producción
- **Tipo:** `[SEC]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F07-04

**Tareas:**
- [ ] Verificar que la clave de cifrado viene de variable de entorno (no hardcodeada)
- [ ] Verificar que el valor cifrado en BD es ilegible sin la clave
- [ ] Verificar que la rotación de clave tiene un procedimiento documentado

---

#### #F07-28 — Verificación final de FASE 07
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] Flujo completo RECEIVED → DELIVERED funciona
- [ ] No se puede saltar estados inválidos
- [ ] Cada cambio de estado registrado en history
- [ ] Credenciales almacenadas cifradas, visualización auditada
- [ ] Repuestos controlados por InventoryMovement
- [ ] Cancelación devuelve stock reservado automáticamente
- [ ] No se puede entregar sin cobro previo
- [ ] Garantía creada automáticamente al entregar
- [ ] Vista móvil funcional para técnico
- [ ] Consulta pública por código REP-... sin login
- [ ] WhatsApp integrado en eventos de reparación
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §15 Reparaciones*
*Fase anterior: [FASE 06](FASE-06-cotizaciones-whatsapp.md) | Siguiente fase: [FASE 08](FASE-08-mantenimientos-instalaciones-envios.md)*
