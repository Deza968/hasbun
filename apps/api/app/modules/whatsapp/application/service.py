"""Servicio de WhatsApp con cola asíncrona y retry (#F06-09).

Reglas clave (REQUIREMENTS §23.4):
- Los envíos son SIEMPRE asíncronos vía Celery; nunca bloquean el flujo principal.
- `send_event` solo crea WhatsAppMessage(PENDING) y encola — retorna de inmediato.
- `process_message` (worker) llama al proveedor; en fallo reintenta con
  backoff 1min → 5min → 15min; tras 3 fallos status=FAILED + notificación OWNER.
- Idempotencia por `idempotency_key` UNIQUE: el mismo evento nunca se envía dos veces.

Los hooks de eventos (#F06-10) llaman a `send_event` DESPUÉS del commit,
dentro de try/except: un fallo de notificación jamás rompe la operación de negocio.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.config import settings
from app.modules.whatsapp.domain.models import (
    WhatsAppConfig,
    WhatsAppDeliveryLog,
    WhatsAppMessage,
    WhatsAppMessageStatus,
    WhatsAppTemplate,
)
from app.modules.whatsapp.infrastructure.provider import WhatsAppSendResult, get_provider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("hasbun.whatsapp")

# Backoff exponencial según spec: intento 1 → 1min, 2 → 5min, 3 → 15min
RETRY_BACKOFF_MINUTES = [1, 5, 15]
MAX_RETRIES = len(RETRY_BACKOFF_MINUTES)


def render_body(body: str, variables: dict[str, Any]) -> str:
    """Reemplaza `{variable}` en la plantilla. Claves ausentes quedan literales."""
    rendered = body
    for key, value in variables.items():
        rendered = rendered.replace("{" + key + "}", "" if value is None else str(value))
    return rendered


async def module_enabled(db: AsyncSession) -> bool:
    """Switch global del módulo (tabla whatsapp_config, una fila)."""
    row = (await db.execute(select(WhatsAppConfig).limit(1))).scalars().first()
    if row is None:
        row = WhatsAppConfig(enabled=True, provider=settings.WHATSAPP_PROVIDER)
        db.add(row)
        await db.flush()
    return bool(row.enabled)


async def send_event(
    db: AsyncSession,
    *,
    event_type: str,
    recipient: str | None,
    variables: dict[str, Any],
    idempotency_key: str,
) -> WhatsAppMessage | None:
    """Encola un mensaje (PENDING) y dispara el worker. Retorna inmediatamente.

    - Sin destinatario o módulo desactivado → no hace nada (None).
    - Template inexistente/inactivo → no hace nada (None).
    - idempotency_key ya usada → devuelve el mensaje existente sin duplicar.
    """
    if not recipient:
        logger.debug("send_event %s sin destinatario: omitido", event_type)
        return None
    existing = (
        await db.execute(select(WhatsAppMessage).where(WhatsAppMessage.idempotency_key == idempotency_key))
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    template = (
        await db.execute(
            select(WhatsAppTemplate)
            .where(
                WhatsAppTemplate.event_type == event_type, WhatsAppTemplate.active.is_(True)
            )
            .order_by(WhatsAppTemplate.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    if template is None or not await module_enabled(db):
        logger.warning("Template activo no encontrado para %s; mensaje omitido", event_type)
        return None

    message = WhatsAppMessage(
        recipient=recipient,
        template_id=template.id,
        payload={
            "template": template.name,
            "event_type": event_type,
            "variables": {k: v for k, v in variables.items()},
            "rendered": render_body(template.body, variables),
        },
        status=WhatsAppMessageStatus.PENDING,
        idempotency_key=idempotency_key[:200],
    )
    db.add(message)
    await db.flush()
    _enqueue(message.id)
    return message


def _enqueue(message_id: uuid.UUID) -> None:
    """Encola la tarea Celery SIN romper el flujo si el broker no está disponible."""
    if not settings.CELERY_ENQUEUE_ENABLED:
        logger.debug("Encolado deshabilitado (tests): WhatsAppMessage %s queda PENDING", message_id)
        return
    try:
        from worker.tasks.whatsapp import send_whatsapp_message

        send_whatsapp_message.delay(str(message_id))
    except Exception:  # noqa: BLE001 — el mensaje queda PENDING para reintento manual/beat
        logger.exception("No se pudo encolar WhatsAppMessage %s (broker caído?)", message_id)


async def process_message(db: AsyncSession, message_id: uuid.UUID) -> WhatsAppMessage:
    """Ejecutado por el worker: intenta enviar un mensaje PENDING/reintentable."""
    message = await db.get(WhatsAppMessage, message_id)
    if message is None:
        raise ValueError(f"WhatsAppMessage {message_id} no existe")
    if message.status in (WhatsAppMessageStatus.SENT, WhatsAppMessageStatus.DELIVERED):
        return message  # idempotente: ya enviado

    attempt = message.retry_count + 1
    provider = get_provider()
    try:
        result = await provider.send_message(
            recipient=message.recipient,
            template_name=str(message.payload.get("template", "")),
            variables=dict(message.payload.get("variables", {})),
            rendered_body=str(message.payload.get("rendered", "")),
        )
    except Exception as exc:  # noqa: BLE001 — stubs NotImplementedError también fallan aquí
        result = WhatsAppSendResult(ok=False, error=str(exc))

    now = datetime.now(UTC)
    db.add(
        WhatsAppDeliveryLog(
            message_id=message.id,
            attempt_number=attempt,
            status="SENT" if result.ok else "FAILED",
            provider_response=result.raw_response,
            attempted_at=now,
            error=result.error,
        )
    )
    if result.ok:
        message.status = WhatsAppMessageStatus.SENT
        message.sent_at = now
        message.provider_message_id = result.provider_message_id
        message.error = None
    else:
        message.retry_count = attempt
        message.error = result.error
        if attempt >= MAX_RETRIES:
            message.status = WhatsAppMessageStatus.FAILED
            message.next_retry_at = None
            # commit primero: la notificación interna es transacción aparte
            await db.commit()
            await _notify_owner_failure(db, message)
            return await db.get(WhatsAppMessage, message.id)  # type: ignore[return-value]
        delay = RETRY_BACKOFF_MINUTES[min(attempt, MAX_RETRIES) - 1]
        message.status = WhatsAppMessageStatus.PENDING
        message.next_retry_at = now + timedelta(minutes=delay)
    await db.commit()
    return await db.get(WhatsAppMessage, message.id)  # type: ignore[return-value]


async def _notify_owner_failure(db: AsyncSession, message: WhatsAppMessage) -> None:
    """Tras agotar reintentos: notificación interna al OWNER (#F06-09)."""
    try:
        from app.modules.notifications.application.service import notify_roles

        await notify_roles(
            db,
            role_codes=["OWNER"],
            type_="whatsapp_failed",
            title="Mensaje de WhatsApp fallido",
            message=(
                f"El mensaje a {message.recipient} ({message.payload.get('event_type')}) "
                f"falló tras {message.retry_count} intentos: {message.error}"
            ),
            priority="HIGH",
            related_type="whatsapp_message",
            related_id=message.id,
        )
        await db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo notificar fallo de WhatsApp al OWNER")


async def retry_failed(db: AsyncSession, message_id: uuid.UUID) -> WhatsAppMessage:
    """Reintento manual desde panel: resetea contadores y vuelve a encolar."""
    message = await db.get(WhatsAppMessage, message_id)
    if message is None:
        raise ValueError(f"WhatsAppMessage {message_id} no existe")
    if message.status != WhatsAppMessageStatus.FAILED:
        return message
    message.status = WhatsAppMessageStatus.PENDING
    message.retry_count = 0
    message.next_retry_at = None
    await db.commit()
    _enqueue(message.id)
    return message
