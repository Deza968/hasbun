# FASE 06 — Cotizaciones y WhatsApp

**Rama:** `feature/fase-06-cotizaciones`
**Objetivo:** Sistema de cotizaciones con conversión a venta sin reingresar datos. Módulo de WhatsApp desacoplado con templates, cola de mensajes y retry automático.
**Prerrequisito:** FASE 05 completada y mergeada a `develop`.
**Criterio de salida:** Cotización puede convertirse a venta sin reingreso de datos. WhatsApp mock envía mensajes a través de Celery. Los eventos de fases anteriores (venta, cuota, mora) disparan WhatsApp correctamente.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 0 | 22 | 0% |

---

## Issues

### COTIZACIONES

---

#### #F06-01 — Modelos Quote y QuoteItem con migración
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-05 completa

**Tareas:**
- [ ] Crear modelos:
  ```
  Quote:
    id (UUID, PK)
    code (VARCHAR, unique)              — COT-YYYY-XXXXX
    customer_id (UUID, FK → Customer)
    status (ENUM):
      DRAFT/SENT/VIEWED/ACCEPTED/REJECTED/EXPIRED/CONVERTED
    subtotal (NUMERIC(14,2))
    discount_amount (NUMERIC(14,2), default 0)
    total (NUMERIC(14,2))
    currency (VARCHAR(3))
    exchange_rate (NUMERIC(10,4))       — congelado al crear
    exchange_rate_source (VARCHAR)
    exchange_rate_timestamp (TIMESTAMPTZ)
    valid_until (DATE)
    notes (TEXT)
    converted_to_sale_id (UUID, FK → Sale, nullable)
    sent_via_whatsapp (BOOLEAN, default False)
    viewed_at (TIMESTAMPTZ)
    responded_at (TIMESTAMPTZ)
    created_by (UUID, FK → User)
    created_at, updated_at (TIMESTAMPTZ)

  QuoteItem:
    id (UUID, PK)
    quote_id (UUID, FK → Quote)
    product_id (UUID, FK → Product)
    quantity (NUMERIC(14,3))
    unit_price (NUMERIC(14,2))          — precio al momento de la cotización
    discount_amount (NUMERIC(14,2), default 0)
    subtotal (NUMERIC(14,2))
    notes (TEXT)
  ```
- [ ] Migración Alembic

---

#### #F06-02 — Servicio de cotizaciones: CRUD y flujo de estados
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-01

**Tareas:**
- [ ] Crear `QuoteService`:
  - `create_quote(customer_id, items, valid_until, notes, user)` → Quote(DRAFT)
  - `send_quote(quote_id, user)`:
    - Quote.status = SENT
    - Dispara evento WhatsApp: QUOTE_CREATED
  - `mark_viewed(quote_id)` — cuando cliente abre el link
  - `accept_quote(quote_id, customer_or_user)`:
    - Quote.status = ACCEPTED
    - AuditLog
    - Notificación a OWNER y SALES
  - `reject_quote(quote_id, reason, customer_or_user)`:
    - Quote.status = REJECTED
    - AuditLog
  - `expire_quote(quote_id)` — ejecutado por tarea Celery
- [ ] Endpoints:
  - `GET /api/v1/quotes` — lista con filtros (estado, cliente, fecha, vendedor)
  - `POST /api/v1/quotes` — crear (OWNER y SALES)
  - `GET /api/v1/quotes/{id}` — detalle
  - `PUT /api/v1/quotes/{id}` — editar si DRAFT
  - `POST /api/v1/quotes/{id}/send` — enviar
  - `POST /api/v1/quotes/{id}/accept` — aceptar
  - `POST /api/v1/quotes/{id}/reject` — rechazar
  - `GET /api/v1/quotes/{code}/public` — vista pública por código (para cliente sin login)

---

#### #F06-03 — Conversión de cotización a venta (operación atómica)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-02

**Descripción:**
Una cotización aceptada se convierte en venta sin reingresar los productos. La operación es atómica.

**Tareas:**
- [ ] Implementar `convert_quote_to_sale(quote_id, sale_type, payment_info, user)`:
  ```
  [TRANSACCIÓN ATÓMICA]:
  1. Verificar quote.status == ACCEPTED
  2. Verificar que quote no está EXPIRED
  3. Para cada QuoteItem: verificar stock disponible
  4. Crear Sale usando los datos de la cotización (no reingreso manual)
  5. Crear SaleItem × N desde QuoteItem × N
  6. Si sale_type = CASH: flujo de venta al contado completo
  7. Si sale_type = CREDIT: flujo de crédito completo
  8. Quote.status = CONVERTED
  9. Quote.converted_to_sale_id = sale.id
  10. AuditLog: CONVERT_QUOTE
  SI CUALQUIER PARTE FALLA: ROLLBACK
  ```
- [ ] No permitir conversión de cotización expirada → 400
- [ ] No permitir conversión de cotización ya convertida → 409
- [ ] Endpoint: `POST /api/v1/quotes/{id}/convert`

---

#### #F06-04 — Tarea Celery: expiración automática de cotizaciones
- **Tipo:** `[TASK]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-02

**Tareas:**
- [ ] Crear tarea `expire_pending_quotes()`:
  - Busca quotes con `valid_until < hoy` y status IN (DRAFT, SENT, VIEWED)
  - Actualiza status = EXPIRED
  - Notificación interna al OWNER y SALES
- [ ] Configurar en Beat: diariamente a las 7 AM
- [ ] Idempotente: no afecta quotes ya expiradas

---

#### #F06-05 — Frontend de cotizaciones (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-02

**Tareas:**
- [ ] `apps/web/app/admin/cotizaciones/page.tsx` — lista con estados y filtros
- [ ] Badge de estado con colores diferenciados
- [ ] `apps/web/app/admin/cotizaciones/nueva/page.tsx` — formulario:
  - Selección de cliente
  - Búsqueda y selección de productos
  - Cantidades y precios (editables)
  - Fecha de validez
  - Notas y condiciones
  - Preview del total con tipo de cambio actual
- [ ] `apps/web/app/admin/cotizaciones/[id]/page.tsx` — detalle:
  - Información completa de la cotización
  - Botones de acción según estado: Enviar, Marcar Aceptada, Convertir a Venta
  - Al "Convertir": modal de selección de tipo de venta (contado/crédito) + datos de pago
- [ ] Vista pública de cotización (sin login): `apps/web/app/(public)/cotizacion/[code]/page.tsx`
  - El cliente puede ver y responder Aceptar/Rechazar
  - No requiere cuenta de cliente

---

#### #F06-06 — Portal del cliente: mis cotizaciones
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-02

**Tareas:**
- [ ] `apps/web/app/customer/cotizaciones/page.tsx` — lista de cotizaciones del cliente
- [ ] Ver detalle y responder (aceptar/rechazar) si status = SENT o VIEWED

---

### WHATSAPP

---

#### #F06-07 — Interfaz WhatsAppProvider y modelos
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-05 completa

**Descripción:**
La aplicación no debe acoplarse a ningún proveedor de WhatsApp específico.

**Tareas:**
- [ ] Crear interfaz `WhatsAppProvider` (ABC):
  ```python
  class WhatsAppProvider(ABC):
      @abstractmethod
      async def send_message(
          self,
          recipient: str,
          template_name: str,
          variables: dict
      ) -> WhatsAppSendResult:
          ...
  ```
- [ ] Crear modelos:
  ```
  WhatsAppTemplate:
    id (UUID, PK)
    name (VARCHAR, unique)
    event_type (ENUM): NEW_SALE/PAYMENT_RECEIVED/INSTALLMENT_UPCOMING/
                       INSTALLMENT_OVERDUE/MORA_CREATED/REPAIR_CREATED/
                       REPAIR_READY/QUOTE_CREATED/QUOTE_ACCEPTED/
                       INSTALLATION_CREATED/INSTALLATION_UPCOMING/
                       STOCK_LOW/STOCK_OUT/WARRANTY_EXPIRING/SALE_COMPLETED
    body (TEXT)
    variables (JSONB)      — lista de variables esperadas: ["customer_name", "amount"]
    active (BOOLEAN)
    created_at (TIMESTAMPTZ)

  WhatsAppMessage:
    id (UUID, PK)
    recipient (VARCHAR, not null)
    template_id (UUID, FK → WhatsAppTemplate)
    payload (JSONB)              — variables ya reemplazadas
    status (ENUM): PENDING/SENT/DELIVERED/FAILED
    idempotency_key (VARCHAR, unique)
    provider_message_id (VARCHAR)
    sent_at (TIMESTAMPTZ)
    error (TEXT)
    retry_count (INTEGER, default 0)
    next_retry_at (TIMESTAMPTZ)
    created_at (TIMESTAMPTZ)

  WhatsAppDeliveryLog:
    id (UUID, PK)
    message_id (UUID, FK → WhatsAppMessage)
    attempt_number (INTEGER)
    status (VARCHAR)
    provider_response (JSONB)
    attempted_at (TIMESTAMPTZ)
    error (TEXT)
  ```
- [ ] Migración Alembic

---

#### #F06-08 — MockWhatsAppProvider
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-07

**Tareas:**
- [ ] Implementar `MockWhatsAppProvider(WhatsAppProvider)`:
  - No hace llamadas HTTP reales
  - Guarda el mensaje en la tabla `WhatsAppMessage` con status=SENT
  - Loguea el mensaje en `stdout` para inspección en desarrollo
  - Simula fallo ocasional si `settings.WHATSAPP_MOCK_FAIL_RATE > 0`
- [ ] La selección del proveedor se hace en `settings.WHATSAPP_PROVIDER`:
  - `"mock"` → MockWhatsAppProvider
  - `"twilio"` → TwilioWhatsAppProvider (preparar stub, no implementar)
  - `"meta"` → MetaWhatsAppProvider (preparar stub, no implementar)

---

#### #F06-09 — Servicio de WhatsApp con cola y retry
- **Tipo:** `[BE]` `[TASK]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-07, #F06-08

**Descripción:**
Los mensajes de WhatsApp son siempre asíncronos. Nunca bloquean el flujo principal.

**Tareas:**
- [ ] Crear `WhatsAppService`:
  - `send_event(event_type, recipient, variables, idempotency_key)`:
    - Busca template activo para event_type
    - Crea `WhatsAppMessage(PENDING)` en BD
    - Encola tarea Celery `send_whatsapp_message.delay(message_id)`
    - Retorna inmediatamente (no espera el envío)
  - `process_message(message_id)` — ejecutado por Celery:
    - Verifica idempotency_key (si ya enviado → skip)
    - Llama `provider.send_message(...)`
    - Si éxito: WhatsAppMessage.status = SENT
    - Si falla: incrementar retry_count
      - Retry 1: esperar 1 minuto
      - Retry 2: esperar 5 minutos
      - Retry 3: esperar 15 minutos
      - Después de 3 intentos: status = FAILED, notificación interna a OWNER
    - Crear WhatsAppDeliveryLog por cada intento
- [ ] Crear `apps/worker/tasks/whatsapp.py`:
  - `send_whatsapp_message(message_id)` — tarea Celery con retry

**Definición de terminado:**
- [ ] Mensaje encolado y procesado asincrónicamente
- [ ] Fallo → retry con backoff exponencial
- [ ] Después de 3 fallos → FAILED + notificación interna
- [ ] Mismo idempotency_key dos veces → no duplica

---

#### #F06-10 — Integrar WhatsApp en eventos existentes (FASE 04 y 05)
- **Tipo:** `[BE]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-09

**Descripción:**
Conectar los eventos de ventas, créditos y mora con el servicio de WhatsApp.

**Tareas:**
- [ ] En `SaleService.create_cash_sale()` (después del commit): encolar `NEW_SALE`
- [ ] En `CreditPaymentService.pay_installment()` (después del commit): encolar `PAYMENT_RECEIVED`
- [ ] En `MoraService.apply_mora_for_period()` (después del commit): encolar `MORA_CREATED` + `INSTALLMENT_OVERDUE`
- [ ] En `CreditService` (tarea programada): 3 días antes del vencimiento → encolar `INSTALLMENT_UPCOMING`
- [ ] En `CreditService.complete_credit()`: encolar `SALE_COMPLETED`

**Nota:** El encolado siempre ocurre DESPUÉS del commit de la transacción principal. Nunca dentro de la transacción.

---

#### #F06-11 — Tarea Celery: recordatorios de cuotas próximas
- **Tipo:** `[TASK]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-09

**Tareas:**
- [ ] Crear tarea `send_upcoming_installment_reminders()`:
  - Busca cuotas con `due_date == hoy + 3 días` y status = PENDING
  - Para cada cuota: encolar WhatsApp `INSTALLMENT_UPCOMING` al cliente
  - Idempotente: no reenvía si ya se envió reminder para esa cuota en el mismo día
- [ ] Configurar en Beat: diariamente a las 9 AM

---

#### #F06-12 — Templates de WhatsApp por defecto
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-07

**Tareas:**
- [ ] Seed de templates para todos los eventos definidos en REQUIREMENTS §23.3
- [ ] Ejemplos:
  ```
  NEW_SALE:
    body: "Hola {customer_name}! Tu compra de {product_list} por S/{total} ha sido registrada.
           Código: {sale_code}. Gracias por preferir Inversiones Hasbun."

  INSTALLMENT_UPCOMING:
    body: "Hola {customer_name}, te recordamos que tu cuota #{installment_number}
           de S/{amount} vence el {due_date}. Código de crédito: {credit_code}."

  REPAIR_READY:
    body: "Hola {customer_name}! Tu equipo {device_brand} {device_model} está listo.
           Orden: {repair_code}. Puedes pasar a recogerlo. Costo: S/{total}."
  ```
- [ ] Templates editables desde panel admin (OWNER puede modificar el `body`)

---

#### #F06-13 — Panel de WhatsApp (admin)
- **Tipo:** `[FE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-09

**Tareas:**
- [ ] `apps/web/app/admin/notificaciones/whatsapp/page.tsx`:
  - Lista de mensajes enviados (con estado: SENT/FAILED/PENDING)
  - Filtros: estado, tipo de evento, fecha
  - Detalle de mensaje: destinatario, contenido enviado, intentos
  - Botón de reintento manual para mensajes FAILED
- [ ] `apps/web/app/admin/configuracion/whatsapp/page.tsx`:
  - Gestión de templates (solo OWNER puede editar)
  - Switch para activar/desactivar el módulo

---

### NOTIFICACIONES INTERNAS

---

#### #F06-14 — Sistema de notificaciones internas
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** FASE-05 completa

**Descripción:**
Notificaciones internas del sistema (diferentes a WhatsApp). Cada rol recibe solo las relevantes.

**Tareas:**
- [ ] Crear modelo `Notification`:
  ```
  Notification:
    id (UUID, PK)
    user_id (UUID, FK → User)
    type (VARCHAR)
    title (VARCHAR)
    message (TEXT)
    read (BOOLEAN, default False)
    priority (ENUM): LOW/MEDIUM/HIGH/URGENT
    related_type (VARCHAR)           — sale / repair / credit / etc.
    related_id (UUID)
    created_at (TIMESTAMPTZ)
    read_at (TIMESTAMPTZ)
  ```
- [ ] Migración
- [ ] Servicio `NotificationService`:
  - `create_notification(user_id, type, title, message, priority, related_type, related_id)`
  - `mark_read(notification_id, user_id)`
  - `mark_all_read(user_id)`
  - `get_unread_count(user_id)`
- [ ] Endpoints:
  - `GET /api/v1/notifications` — mis notificaciones (paginadas)
  - `POST /api/v1/notifications/{id}/read` — marcar leída
  - `POST /api/v1/notifications/read-all` — marcar todas leídas
  - `GET /api/v1/notifications/unread-count` — contador (para badge en header)
- [ ] Integrar con eventos existentes: mora, cierre de caja, descuento solicitado, etc.
- [ ] Polling en frontend cada 30 segundos para contador de no leídas (preparar para WebSocket futuro)

**Definición de terminado:**
- [ ] OWNER recibe notificación cuando SALES solicita descuento
- [ ] OWNER recibe notificación cuando hay cierre de caja pendiente
- [ ] SALES recibe notificación cuando su descuento es aprobado/rechazado
- [ ] Cada rol solo ve sus notificaciones, no las de otros → 403

---

#### #F06-15 — Frontend de notificaciones
- **Tipo:** `[FE]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-14

**Tareas:**
- [ ] Badge de notificaciones no leídas en el header del panel admin
- [ ] Dropdown de notificaciones recientes al hacer clic en el badge
- [ ] `apps/web/app/admin/notificaciones/page.tsx` — lista completa con filtros
- [ ] Al hacer clic en una notificación: marcar como leída y navegar al elemento relacionado
- [ ] Indicador de prioridad: borde de color según urgencia

---

### TESTS

---

#### #F06-16 — Tests de cotizaciones
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-02, #F06-03

**Tareas:**
- [ ] `test_create_quote_freezes_prices` — precios guardados al momento de cotizar
- [ ] `test_convert_quote_to_cash_sale` — conversión atómica sin reingreso de datos
- [ ] `test_convert_quote_to_credit` — conversión a crédito
- [ ] `test_cannot_convert_expired_quote` → 400
- [ ] `test_cannot_convert_already_converted_quote` → 409
- [ ] `test_convert_quote_rollback` — si falla la venta → quote no marcada como CONVERTED
- [ ] `test_quote_expires_automatically` — tarea de expiración funciona
- [ ] `test_sales_can_create_quote` → 201
- [ ] `test_technician_cannot_create_quote` → 403

---

#### #F06-17 — Tests de WhatsApp
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-09

**Tareas:**
- [ ] `test_whatsapp_message_queued_after_sale` — venta exitosa → WhatsAppMessage(PENDING) en cola
- [ ] `test_whatsapp_message_sent_by_worker` — worker procesa → status=SENT
- [ ] `test_whatsapp_retry_on_failure` — fallo → retry con backoff
- [ ] `test_whatsapp_failed_after_max_retries` — 3 fallos → status=FAILED
- [ ] `test_whatsapp_idempotency` — mismo idempotency_key → 1 solo mensaje
- [ ] `test_whatsapp_not_sent_within_transaction` — el encolado ocurre DESPUÉS del commit

---

#### #F06-18 — Tests de notificaciones internas
- **Tipo:** `[TEST]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-14

**Tareas:**
- [ ] `test_notification_created_for_correct_user` — llega al usuario correcto según tipo
- [ ] `test_user_cannot_see_other_user_notifications` → 403
- [ ] `test_mark_notification_read` — unread_count disminuye
- [ ] `test_notification_priority_levels` — URGENT creado correctamente

---

### DOCUMENTACIÓN

---

#### #F06-19 — Documentar WhatsApp en docs/whatsapp.md
- **Tipo:** `[DOCS]`
- **Prioridad:** 🟠 ALTO
- **Estado:** ⬜ Pendiente

**Tareas:**
- [ ] Documentar la arquitectura del proveedor (interfaz + implementaciones)
- [ ] Documentar el flujo de envío asíncrono con Celery
- [ ] Documentar la estrategia de retry y backoff
- [ ] Documentar cómo agregar un nuevo proveedor de WhatsApp
- [ ] Documentar todos los eventos y sus templates
- [ ] Instrucciones para configurar proveedor externo en producción

---

### SEEDS

---

#### #F06-20 — Seeds de cotizaciones y templates de WhatsApp
- **Tipo:** `[BE]`
- **Prioridad:** 🟡 MEDIO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-12

**Tareas:**
- [ ] 3 cotizaciones ficticias (SENT, ACCEPTED, EXPIRED)
- [ ] Templates de WhatsApp para todos los eventos (datos ficticios de ejemplo)
- [ ] 5 mensajes de WhatsApp ficticios en estados varios (SENT, FAILED)

---

### VERIFICACIÓN FINAL

---

#### #F06-21 — Integración end-to-end: venta → WhatsApp
- **Tipo:** `[TEST]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** #F06-10

**Tareas:**
- [ ] Test de integración completo:
  1. Crear venta al contado
  2. Verificar que WhatsAppMessage(PENDING) fue creado
  3. Ejecutar worker
  4. Verificar que WhatsAppMessage.status = SENT
  5. Verificar contenido del mensaje (variables reemplazadas correctamente)

---

#### #F06-22 — Verificación final de FASE 06
- **Tipo:** `[INFRA]`
- **Prioridad:** 🔴 CRÍTICO
- **Estado:** ⬜ Pendiente
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] CRUD de cotizaciones completo con estados correctos
- [ ] Cotización aceptada se convierte a venta sin reingreso de datos
- [ ] Cotización expirada no puede convertirse → 400
- [ ] WhatsApp desacoplado del proveedor (interfaz)
- [ ] Mensajes siempre asíncronos (nunca bloquean el flujo principal)
- [ ] Retry con backoff exponencial (1min, 5min, 15min)
- [ ] Después de 3 fallos: FAILED + notificación interna al OWNER
- [ ] Idempotencia: mismo mensaje no se envía dos veces
- [ ] Eventos de ventas, cuotas y mora disparan WhatsApp
- [ ] Notificaciones internas llegan al rol correcto
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) §14 Cotizaciones, §23 WhatsApp, §24 Notificaciones*
*Fase anterior: [FASE 05](FASE-05-creditos-cuotas-mora.md) | Siguiente fase: [FASE 07](FASE-07-reparaciones.md)*
