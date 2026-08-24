# Módulo de WhatsApp (#F06)

## Arquitectura

El módulo es **desacoplado del resto del sistema**: ningún flujo de negocio
espera a WhatsApp. Los envíos son siempre **asíncronos vía Celery**.

```
Evento de negocio (post-commit)
        │  send_event(event_type, recipient, variables, idempotency_key)
        ▼
WhatsAppMessage (PENDING)  ──►  cola Celery (worker.tasks.whatsapp)
        │                              │
        │                    process_message → proveedor
        │                              │
        ├─ OK ──► status=SENT + WhatsAppDeliveryLog(SENT)
        │
        └─ FALLO ──► reintento con backoff: +1min → +5min → +15min
                          │ tras 3 intentos fallidos
                          ▼
                 status=FAILED + notificación interna al OWNER
```

### Reglas clave (REQUIREMENTS §23.4)

- **Nunca dentro de la transacción**: los hooks se ejecutan después del
  `commit` y dentro de `try/except`; un fallo de WhatsApp jamás revierte
  una venta, pago o cotización.
- **Idempotencia**: cada mensaje lleva una `idempotency_key` única
  (`UNIQUE` en BD). Reenviar el mismo evento no duplica el mensaje.
- **Reintentos**: backoff fijo `[1, 5, 15]` minutos (`RETRY_BACKOFF_MINUTES`);
  tras el tercer fallo el mensaje queda `FAILED` y el OWNER recibe una
  notificación interna. Desde el panel se puede reintentar manualmente.
- **Switch global**: la tabla `whatsapp_config` permite desactivar todo el
  módulo sin tocar código (`module_enabled`).

## Eventos soportados (#F06-10)

| Evento | Disparador | Idempotency key |
|---|---|---|
| `NEW_SALE` | Venta contado creada | `new-sale:{sale_id}` |
| `PAYMENT_RECEIVED` | Pago de cuota registrado | `payment-received:{installment_id}:{monto}` |
| `SALE_COMPLETED` | Última cuota pagada | `sale-completed:{agreement_id}` |
| `MORA_CREATED` | Tarea diaria genera mora | `mora-created:{installment_id}:{periodo}` |
| `INSTALLMENT_OVERDUE` | Cuota vencida detectada | `installment-overdue:{installment_id}:{periodo}` |
| `INSTALLMENT_UPCOMING` | Recordatorio +3 días (9AM) | `installment-upcoming:{installment_id}:{fecha}` |
| `QUOTE_CREATED` | Cotización enviada | `quote-created:{quote_id}` |
| `QUOTE_ACCEPTED` | Cliente acepta cotización (aviso OWNER) | `quote-accepted:{quote_id}` |

Reservados para fases futuras: `REPAIR_*`, `INSTALLATION_*`, `STOCK_LOW`,
`STOCK_OUT`, `WARRANTY_EXPIRING`.

## Plantillas

Tabla `whatsapp_templates`: nombre único, `event_type`, cuerpo con variables
`{nombre}`, lista de variables e indicador `active`. El seed crea las 15
plantillas. Solo OWNER (`configuracion.editar`) puede editarlas o
desactivarlas desde el panel.

Variables ausentes quedan como texto literal `{variable}`.

## Proveedores

`WHATSAPP_PROVIDER` en configuración:

- `mock` (default): imprime el mensaje en logs; `WHATSAPP_MOCK_FAIL_RATE`
  simula fallos para probar reintentos.
- `twilio` / `meta`: stubs listos para implementar (`NotImplementedError`),
  misma interfaz `WhatsAppProvider`.

## Panel admin (#F06-13)

Ruta `/admin/whatsapp`, permiso `whatsapp.gestionar`:

- Lista de mensajes con filtros por estado/evento.
- Reintento manual de mensajes `FAILED`.
- Plantillas (ver/editar según permiso).
- Switch on/off del módulo (requiere `configuracion.editar`).

## Notificaciones internas (#F06-11/#F06-12)

Paralelo al canal cliente, `notifications` avisa al staff:

- OWNER/SALES: cotización aceptada/expirada, cuotas vencidas con mora.
- OWNER: solicitud de descuento, cierre de caja con diferencia,
  mensaje WhatsApp fallido, nuevo crédito.
- SALES: resultado de su solicitud de descuento (aprobada/rechazada).

API `/api/v1/notifications` por usuario autenticado (lista, unread-count,
marcar leída, marcar todas). El frontend muestra campana con contador
(polling 30s).
