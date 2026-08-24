# FASE 06 â€” Cotizaciones y WhatsApp

**Rama:** `feature/fase-06-cotizaciones`
**Objetivo:** Sistema de cotizaciones con conversiÃ³n a venta sin reingresar datos. MÃ³dulo de WhatsApp desacoplado con templates, cola de mensajes y retry automÃ¡tico.
**Prerrequisito:** FASE 05 completada y mergeada a `develop`.
**Criterio de salida:** CotizaciÃ³n puede convertirse a venta sin reingreso de datos. WhatsApp mock envÃ­a mensajes a travÃ©s de Celery. Los eventos de fases anteriores (venta, cuota, mora) disparan WhatsApp correctamente.

---

## Progreso

| Completados | Total | Porcentaje |
|---|---|---|
| 22 | 22 | 100% |

> **Verificación 2026-08-24:** backend completo (modelos + migración e6f7a8b9c0d1, servicios, routers, worker con beat: expiración 7AM, recordatorios 9AM, retry WhatsApp */15min). Suite pytest completa verde (incluye test_quotes/test_whatsapp/test_notifications), ruff y mypy limpios en 298 archivos. Migración aplicada a BD dev y seeds verificados (3 cotizaciones SENT/ACCEPTED/EXPIRED, 15 plantillas, 5 mensajes muestra). Hooks WhatsApp/notificaciones integrados en ventas, créditos, mora, cotizaciones, descuentos y cierres de caja. Frontend: admin cotizaciones (lista/nueva/detalle+conversión), panel WhatsApp, campana de notificaciones, portal cliente y página pública /cotizacion/[code]. 
ext build OK.

---

## Issues

### COTIZACIONES

---

#### #F06-01 â€” Modelos Quote y QuoteItem con migraciÃ³n
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** FASE-05 completa

**Tareas:**
- [ ] Crear modelos:
  ```
  Quote:
    id (UUID, PK)
    code (VARCHAR, unique)              â€” COT-YYYY-XXXXX
    customer_id (UUID, FK â†’ Customer)
    status (ENUM):
      DRAFT/SENT/VIEWED/ACCEPTED/REJECTED/EXPIRED/CONVERTED
    subtotal (NUMERIC(14,2))
    discount_amount (NUMERIC(14,2), default 0)
    total (NUMERIC(14,2))
    currency (VARCHAR(3))
    exchange_rate (NUMERIC(10,4))       â€” congelado al crear
    exchange_rate_source (VARCHAR)
    exchange_rate_timestamp (TIMESTAMPTZ)
    valid_until (DATE)
    notes (TEXT)
    converted_to_sale_id (UUID, FK â†’ Sale, nullable)
    sent_via_whatsapp (BOOLEAN, default False)
    viewed_at (TIMESTAMPTZ)
    responded_at (TIMESTAMPTZ)
    created_by (UUID, FK â†’ User)
    created_at, updated_at (TIMESTAMPTZ)

  QuoteItem:
    id (UUID, PK)
    quote_id (UUID, FK â†’ Quote)
    product_id (UUID, FK â†’ Product)
    quantity (NUMERIC(14,3))
    unit_price (NUMERIC(14,2))          â€” precio al momento de la cotizaciÃ³n
    discount_amount (NUMERIC(14,2), default 0)
    subtotal (NUMERIC(14,2))
    notes (TEXT)
  ```
- [ ] MigraciÃ³n Alembic

---

#### #F06-02 â€” Servicio de cotizaciones: CRUD y flujo de estados
- **Tipo:** `[BE]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-01

**Tareas:**
- [ ] Crear `QuoteService`:
  - `create_quote(customer_id, items, valid_until, notes, user)` â†’ Quote(DRAFT)
  - `send_quote(quote_id, user)`:
    - Quote.status = SENT
    - Dispara evento WhatsApp: QUOTE_CREATED
  - `mark_viewed(quote_id)` â€” cuando cliente abre el link
  - `accept_quote(quote_id, customer_or_user)`:
    - Quote.status = ACCEPTED
    - AuditLog
    - NotificaciÃ³n a OWNER y SALES
  - `reject_quote(quote_id, reason, customer_or_user)`:
    - Quote.status = REJECTED
    - AuditLog
  - `expire_quote(quote_id)` â€” ejecutado por tarea Celery
- [ ] Endpoints:
  - `GET /api/v1/quotes` â€” lista con filtros (estado, cliente, fecha, vendedor)
  - `POST /api/v1/quotes` â€” crear (OWNER y SALES)
  - `GET /api/v1/quotes/{id}` â€” detalle
  - `PUT /api/v1/quotes/{id}` â€” editar si DRAFT
  - `POST /api/v1/quotes/{id}/send` â€” enviar
  - `POST /api/v1/quotes/{id}/accept` â€” aceptar
  - `POST /api/v1/quotes/{id}/reject` â€” rechazar
  - `GET /api/v1/quotes/{code}/public` â€” vista pÃºblica por cÃ³digo (para cliente sin login)

---

#### #F06-03 â€” ConversiÃ³n de cotizaciÃ³n a venta (operaciÃ³n atÃ³mica)
- **Tipo:** `[BE]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-02

**DescripciÃ³n:**
Una cotizaciÃ³n aceptada se convierte en venta sin reingresar los productos. La operaciÃ³n es atÃ³mica.

**Tareas:**
- [ ] Implementar `convert_quote_to_sale(quote_id, sale_type, payment_info, user)`:
  ```
  [TRANSACCIÃ“N ATÃ“MICA]:
  1. Verificar quote.status == ACCEPTED
  2. Verificar que quote no estÃ¡ EXPIRED
  3. Para cada QuoteItem: verificar stock disponible
  4. Crear Sale usando los datos de la cotizaciÃ³n (no reingreso manual)
  5. Crear SaleItem Ã— N desde QuoteItem Ã— N
  6. Si sale_type = CASH: flujo de venta al contado completo
  7. Si sale_type = CREDIT: flujo de crÃ©dito completo
  8. Quote.status = CONVERTED
  9. Quote.converted_to_sale_id = sale.id
  10. AuditLog: CONVERT_QUOTE
  SI CUALQUIER PARTE FALLA: ROLLBACK
  ```
- [ ] No permitir conversiÃ³n de cotizaciÃ³n expirada â†’ 400
- [ ] No permitir conversiÃ³n de cotizaciÃ³n ya convertida â†’ 409
- [ ] Endpoint: `POST /api/v1/quotes/{id}/convert`

---

#### #F06-04 â€” Tarea Celery: expiraciÃ³n automÃ¡tica de cotizaciones
- **Tipo:** `[TASK]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** #F06-02

**Tareas:**
- [ ] Crear tarea `expire_pending_quotes()`:
  - Busca quotes con `valid_until < hoy` y status IN (DRAFT, SENT, VIEWED)
  - Actualiza status = EXPIRED
  - NotificaciÃ³n interna al OWNER y SALES
- [ ] Configurar en Beat: diariamente a las 7 AM
- [ ] Idempotente: no afecta quotes ya expiradas

---

#### #F06-05 â€” Frontend de cotizaciones (admin)
- **Tipo:** `[FE]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** #F06-02

**Tareas:**
- [ ] `apps/web/app/admin/cotizaciones/page.tsx` â€” lista con estados y filtros
- [ ] Badge de estado con colores diferenciados
- [ ] `apps/web/app/admin/cotizaciones/nueva/page.tsx` â€” formulario:
  - SelecciÃ³n de cliente
  - BÃºsqueda y selecciÃ³n de productos
  - Cantidades y precios (editables)
  - Fecha de validez
  - Notas y condiciones
  - Preview del total con tipo de cambio actual
- [ ] `apps/web/app/admin/cotizaciones/[id]/page.tsx` â€” detalle:
  - InformaciÃ³n completa de la cotizaciÃ³n
  - Botones de acciÃ³n segÃºn estado: Enviar, Marcar Aceptada, Convertir a Venta
  - Al "Convertir": modal de selecciÃ³n de tipo de venta (contado/crÃ©dito) + datos de pago
- [ ] Vista pÃºblica de cotizaciÃ³n (sin login): `apps/web/app/(public)/cotizacion/[code]/page.tsx`
  - El cliente puede ver y responder Aceptar/Rechazar
  - No requiere cuenta de cliente

---

#### #F06-06 â€” Portal del cliente: mis cotizaciones
- **Tipo:** `[FE]`
- **Prioridad:** ðŸŸ¡ MEDIO
- **Estado:** ✅ Completada
- **Depende de:** #F06-02

**Tareas:**
- [ ] `apps/web/app/customer/cotizaciones/page.tsx` â€” lista de cotizaciones del cliente
- [ ] Ver detalle y responder (aceptar/rechazar) si status = SENT o VIEWED

---

### WHATSAPP

---

#### #F06-07 â€” Interfaz WhatsAppProvider y modelos
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** FASE-05 completa

**DescripciÃ³n:**
La aplicaciÃ³n no debe acoplarse a ningÃºn proveedor de WhatsApp especÃ­fico.

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
    variables (JSONB)      â€” lista de variables esperadas: ["customer_name", "amount"]
    active (BOOLEAN)
    created_at (TIMESTAMPTZ)

  WhatsAppMessage:
    id (UUID, PK)
    recipient (VARCHAR, not null)
    template_id (UUID, FK â†’ WhatsAppTemplate)
    payload (JSONB)              â€” variables ya reemplazadas
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
    message_id (UUID, FK â†’ WhatsAppMessage)
    attempt_number (INTEGER)
    status (VARCHAR)
    provider_response (JSONB)
    attempted_at (TIMESTAMPTZ)
    error (TEXT)
  ```
- [ ] MigraciÃ³n Alembic

---

#### #F06-08 â€” MockWhatsAppProvider
- **Tipo:** `[BE]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-07

**Tareas:**
- [ ] Implementar `MockWhatsAppProvider(WhatsAppProvider)`:
  - No hace llamadas HTTP reales
  - Guarda el mensaje en la tabla `WhatsAppMessage` con status=SENT
  - Loguea el mensaje en `stdout` para inspecciÃ³n en desarrollo
  - Simula fallo ocasional si `settings.WHATSAPP_MOCK_FAIL_RATE > 0`
- [ ] La selecciÃ³n del proveedor se hace en `settings.WHATSAPP_PROVIDER`:
  - `"mock"` â†’ MockWhatsAppProvider
  - `"twilio"` â†’ TwilioWhatsAppProvider (preparar stub, no implementar)
  - `"meta"` â†’ MetaWhatsAppProvider (preparar stub, no implementar)

---

#### #F06-09 â€” Servicio de WhatsApp con cola y retry
- **Tipo:** `[BE]` `[TASK]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-07, #F06-08

**DescripciÃ³n:**
Los mensajes de WhatsApp son siempre asÃ­ncronos. Nunca bloquean el flujo principal.

**Tareas:**
- [ ] Crear `WhatsAppService`:
  - `send_event(event_type, recipient, variables, idempotency_key)`:
    - Busca template activo para event_type
    - Crea `WhatsAppMessage(PENDING)` en BD
    - Encola tarea Celery `send_whatsapp_message.delay(message_id)`
    - Retorna inmediatamente (no espera el envÃ­o)
  - `process_message(message_id)` â€” ejecutado por Celery:
    - Verifica idempotency_key (si ya enviado â†’ skip)
    - Llama `provider.send_message(...)`
    - Si Ã©xito: WhatsAppMessage.status = SENT
    - Si falla: incrementar retry_count
      - Retry 1: esperar 1 minuto
      - Retry 2: esperar 5 minutos
      - Retry 3: esperar 15 minutos
      - DespuÃ©s de 3 intentos: status = FAILED, notificaciÃ³n interna a OWNER
    - Crear WhatsAppDeliveryLog por cada intento
- [ ] Crear `apps/worker/tasks/whatsapp.py`:
  - `send_whatsapp_message(message_id)` â€” tarea Celery con retry

**DefiniciÃ³n de terminado:**
- [ ] Mensaje encolado y procesado asincrÃ³nicamente
- [ ] Fallo â†’ retry con backoff exponencial
- [ ] DespuÃ©s de 3 fallos â†’ FAILED + notificaciÃ³n interna
- [ ] Mismo idempotency_key dos veces â†’ no duplica

---

#### #F06-10 â€” Integrar WhatsApp en eventos existentes (FASE 04 y 05)
- **Tipo:** `[BE]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-09

**DescripciÃ³n:**
Conectar los eventos de ventas, crÃ©ditos y mora con el servicio de WhatsApp.

**Tareas:**
- [ ] En `SaleService.create_cash_sale()` (despuÃ©s del commit): encolar `NEW_SALE`
- [ ] En `CreditPaymentService.pay_installment()` (despuÃ©s del commit): encolar `PAYMENT_RECEIVED`
- [ ] En `MoraService.apply_mora_for_period()` (despuÃ©s del commit): encolar `MORA_CREATED` + `INSTALLMENT_OVERDUE`
- [ ] En `CreditService` (tarea programada): 3 dÃ­as antes del vencimiento â†’ encolar `INSTALLMENT_UPCOMING`
- [ ] En `CreditService.complete_credit()`: encolar `SALE_COMPLETED`

**Nota:** El encolado siempre ocurre DESPUÃ‰S del commit de la transacciÃ³n principal. Nunca dentro de la transacciÃ³n.

---

#### #F06-11 â€” Tarea Celery: recordatorios de cuotas prÃ³ximas
- **Tipo:** `[TASK]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** #F06-09

**Tareas:**
- [ ] Crear tarea `send_upcoming_installment_reminders()`:
  - Busca cuotas con `due_date == hoy + 3 dÃ­as` y status = PENDING
  - Para cada cuota: encolar WhatsApp `INSTALLMENT_UPCOMING` al cliente
  - Idempotente: no reenvÃ­a si ya se enviÃ³ reminder para esa cuota en el mismo dÃ­a
- [ ] Configurar en Beat: diariamente a las 9 AM

---

#### #F06-12 â€” Templates de WhatsApp por defecto
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** #F06-07

**Tareas:**
- [ ] Seed de templates para todos los eventos definidos en REQUIREMENTS Â§23.3
- [ ] Ejemplos:
  ```
  NEW_SALE:
    body: "Hola {customer_name}! Tu compra de {product_list} por S/{total} ha sido registrada.
           CÃ³digo: {sale_code}. Gracias por preferir Inversiones Hasbun."

  INSTALLMENT_UPCOMING:
    body: "Hola {customer_name}, te recordamos que tu cuota #{installment_number}
           de S/{amount} vence el {due_date}. CÃ³digo de crÃ©dito: {credit_code}."

  REPAIR_READY:
    body: "Hola {customer_name}! Tu equipo {device_brand} {device_model} estÃ¡ listo.
           Orden: {repair_code}. Puedes pasar a recogerlo. Costo: S/{total}."
  ```
- [ ] Templates editables desde panel admin (OWNER puede modificar el `body`)

---

#### #F06-13 â€” Panel de WhatsApp (admin)
- **Tipo:** `[FE]`
- **Prioridad:** ðŸŸ¡ MEDIO
- **Estado:** ✅ Completada
- **Depende de:** #F06-09

**Tareas:**
- [ ] `apps/web/app/admin/notificaciones/whatsapp/page.tsx`:
  - Lista de mensajes enviados (con estado: SENT/FAILED/PENDING)
  - Filtros: estado, tipo de evento, fecha
  - Detalle de mensaje: destinatario, contenido enviado, intentos
  - BotÃ³n de reintento manual para mensajes FAILED
- [ ] `apps/web/app/admin/configuracion/whatsapp/page.tsx`:
  - GestiÃ³n de templates (solo OWNER puede editar)
  - Switch para activar/desactivar el mÃ³dulo

---

### NOTIFICACIONES INTERNAS

---

#### #F06-14 â€” Sistema de notificaciones internas
- **Tipo:** `[BE]` `[DB]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** FASE-05 completa

**DescripciÃ³n:**
Notificaciones internas del sistema (diferentes a WhatsApp). Cada rol recibe solo las relevantes.

**Tareas:**
- [ ] Crear modelo `Notification`:
  ```
  Notification:
    id (UUID, PK)
    user_id (UUID, FK â†’ User)
    type (VARCHAR)
    title (VARCHAR)
    message (TEXT)
    read (BOOLEAN, default False)
    priority (ENUM): LOW/MEDIUM/HIGH/URGENT
    related_type (VARCHAR)           â€” sale / repair / credit / etc.
    related_id (UUID)
    created_at (TIMESTAMPTZ)
    read_at (TIMESTAMPTZ)
  ```
- [ ] MigraciÃ³n
- [ ] Servicio `NotificationService`:
  - `create_notification(user_id, type, title, message, priority, related_type, related_id)`
  - `mark_read(notification_id, user_id)`
  - `mark_all_read(user_id)`
  - `get_unread_count(user_id)`
- [ ] Endpoints:
  - `GET /api/v1/notifications` â€” mis notificaciones (paginadas)
  - `POST /api/v1/notifications/{id}/read` â€” marcar leÃ­da
  - `POST /api/v1/notifications/read-all` â€” marcar todas leÃ­das
  - `GET /api/v1/notifications/unread-count` â€” contador (para badge en header)
- [ ] Integrar con eventos existentes: mora, cierre de caja, descuento solicitado, etc.
- [ ] Polling en frontend cada 30 segundos para contador de no leÃ­das (preparar para WebSocket futuro)

**DefiniciÃ³n de terminado:**
- [ ] OWNER recibe notificaciÃ³n cuando SALES solicita descuento
- [ ] OWNER recibe notificaciÃ³n cuando hay cierre de caja pendiente
- [ ] SALES recibe notificaciÃ³n cuando su descuento es aprobado/rechazado
- [ ] Cada rol solo ve sus notificaciones, no las de otros â†’ 403

---

#### #F06-15 â€” Frontend de notificaciones
- **Tipo:** `[FE]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** #F06-14

**Tareas:**
- [ ] Badge de notificaciones no leÃ­das en el header del panel admin
- [ ] Dropdown de notificaciones recientes al hacer clic en el badge
- [ ] `apps/web/app/admin/notificaciones/page.tsx` â€” lista completa con filtros
- [ ] Al hacer clic en una notificaciÃ³n: marcar como leÃ­da y navegar al elemento relacionado
- [ ] Indicador de prioridad: borde de color segÃºn urgencia

---

### TESTS

---

#### #F06-16 â€” Tests de cotizaciones
- **Tipo:** `[TEST]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-02, #F06-03

**Tareas:**
- [ ] `test_create_quote_freezes_prices` â€” precios guardados al momento de cotizar
- [ ] `test_convert_quote_to_cash_sale` â€” conversiÃ³n atÃ³mica sin reingreso de datos
- [ ] `test_convert_quote_to_credit` â€” conversiÃ³n a crÃ©dito
- [ ] `test_cannot_convert_expired_quote` â†’ 400
- [ ] `test_cannot_convert_already_converted_quote` â†’ 409
- [ ] `test_convert_quote_rollback` â€” si falla la venta â†’ quote no marcada como CONVERTED
- [ ] `test_quote_expires_automatically` â€” tarea de expiraciÃ³n funciona
- [ ] `test_sales_can_create_quote` â†’ 201
- [ ] `test_technician_cannot_create_quote` â†’ 403

---

#### #F06-17 â€” Tests de WhatsApp
- **Tipo:** `[TEST]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-09

**Tareas:**
- [ ] `test_whatsapp_message_queued_after_sale` â€” venta exitosa â†’ WhatsAppMessage(PENDING) en cola
- [ ] `test_whatsapp_message_sent_by_worker` â€” worker procesa â†’ status=SENT
- [ ] `test_whatsapp_retry_on_failure` â€” fallo â†’ retry con backoff
- [ ] `test_whatsapp_failed_after_max_retries` â€” 3 fallos â†’ status=FAILED
- [ ] `test_whatsapp_idempotency` â€” mismo idempotency_key â†’ 1 solo mensaje
- [ ] `test_whatsapp_not_sent_within_transaction` â€” el encolado ocurre DESPUÃ‰S del commit

---

#### #F06-18 â€” Tests de notificaciones internas
- **Tipo:** `[TEST]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada
- **Depende de:** #F06-14

**Tareas:**
- [ ] `test_notification_created_for_correct_user` â€” llega al usuario correcto segÃºn tipo
- [ ] `test_user_cannot_see_other_user_notifications` â†’ 403
- [ ] `test_mark_notification_read` â€” unread_count disminuye
- [ ] `test_notification_priority_levels` â€” URGENT creado correctamente

---

### DOCUMENTACIÃ“N

---

#### #F06-19 â€” Documentar WhatsApp en docs/whatsapp.md
- **Tipo:** `[DOCS]`
- **Prioridad:** ðŸŸ  ALTO
- **Estado:** ✅ Completada

**Tareas:**
- [ ] Documentar la arquitectura del proveedor (interfaz + implementaciones)
- [ ] Documentar el flujo de envÃ­o asÃ­ncrono con Celery
- [ ] Documentar la estrategia de retry y backoff
- [ ] Documentar cÃ³mo agregar un nuevo proveedor de WhatsApp
- [ ] Documentar todos los eventos y sus templates
- [ ] Instrucciones para configurar proveedor externo en producciÃ³n

---

### SEEDS

---

#### #F06-20 â€” Seeds de cotizaciones y templates de WhatsApp
- **Tipo:** `[BE]`
- **Prioridad:** ðŸŸ¡ MEDIO
- **Estado:** ✅ Completada
- **Depende de:** #F06-12

**Tareas:**
- [ ] 3 cotizaciones ficticias (SENT, ACCEPTED, EXPIRED)
- [ ] Templates de WhatsApp para todos los eventos (datos ficticios de ejemplo)
- [ ] 5 mensajes de WhatsApp ficticios en estados varios (SENT, FAILED)

---

### VERIFICACIÃ“N FINAL

---

#### #F06-21 â€” IntegraciÃ³n end-to-end: venta â†’ WhatsApp
- **Tipo:** `[TEST]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** #F06-10

**Tareas:**
- [ ] Test de integraciÃ³n completo:
  1. Crear venta al contado
  2. Verificar que WhatsAppMessage(PENDING) fue creado
  3. Ejecutar worker
  4. Verificar que WhatsAppMessage.status = SENT
  5. Verificar contenido del mensaje (variables reemplazadas correctamente)

---

#### #F06-22 â€” VerificaciÃ³n final de FASE 06
- **Tipo:** `[INFRA]`
- **Prioridad:** ðŸ”´ CRÃTICO
- **Estado:** ✅ Completada
- **Depende de:** Todos los anteriores

**Checklist de salida de fase:**
- [ ] CRUD de cotizaciones completo con estados correctos
- [ ] CotizaciÃ³n aceptada se convierte a venta sin reingreso de datos
- [ ] CotizaciÃ³n expirada no puede convertirse â†’ 400
- [ ] WhatsApp desacoplado del proveedor (interfaz)
- [ ] Mensajes siempre asÃ­ncronos (nunca bloquean el flujo principal)
- [ ] Retry con backoff exponencial (1min, 5min, 15min)
- [ ] DespuÃ©s de 3 fallos: FAILED + notificaciÃ³n interna al OWNER
- [ ] Idempotencia: mismo mensaje no se envÃ­a dos veces
- [ ] Eventos de ventas, cuotas y mora disparan WhatsApp
- [ ] Notificaciones internas llegan al rol correcto
- [ ] CI verde
- [ ] PR mergeado a `develop`

---

*Referencia: [REQUIREMENTS.md](../REQUIREMENTS.md) Â§14 Cotizaciones, Â§23 WhatsApp, Â§24 Notificaciones*
*Fase anterior: [FASE 05](FASE-05-creditos-cuotas-mora.md) | Siguiente fase: [FASE 07](FASE-07-reparaciones.md)*
