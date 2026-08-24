"""Tareas Celery de WhatsApp (#F06-09).

`send_whatsapp_message` procesa un mensaje PENDING con retry/backoff
(1min → 5min → 15min). El backoff real lo gestiona `WhatsAppService.
process_message` (next_retry_at + status), de modo que la tarea es
idempotente y segura ante dobles ejecuciones.
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker.whatsapp")


async def _run(message_id: str) -> dict[str, object]:
    from app.database.session import AsyncSessionLocal
    from app.modules.whatsapp.application.service import process_message

    async with AsyncSessionLocal() as db:
        message = await process_message(db, uuid.UUID(message_id))
        return {"message_id": message_id, "status": message.status, "retries": message.retry_count}


@celery_app.task(
    name="worker.tasks.whatsapp.send_whatsapp_message",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_whatsapp_message(self, message_id: str) -> dict[str, object]:  # noqa: ANN001
    try:
        result: dict[str, object] = asyncio.run(_run(message_id))
        logger.info("WhatsApp procesado: %s", result)
        return result
    except Exception as exc:  # noqa: BLE001
        logger.exception("Fallo procesando WhatsAppMessage %s", message_id)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


async def _run_sweep() -> dict[str, object]:
    """Reencola PENDING cuyo next_retry_at ya venció (p.ej. broker caído)."""
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.database.session import AsyncSessionLocal
    from app.modules.whatsapp.domain.models import WhatsAppMessage, WhatsAppMessageStatus
    from worker.tasks.whatsapp import send_whatsapp_message as task

    requeued = 0
    async with AsyncSessionLocal() as db:
        rows = await db.execute(
            select(WhatsAppMessage.id).where(WhatsAppMessage.status == WhatsAppMessageStatus.PENDING)
        )
        now = datetime.now(UTC)
        for (mid,) in rows.all():
            message = await db.get(WhatsAppMessage, mid)
            if message is None or message.next_retry_at and message.next_retry_at > now:
                continue
            task.delay(str(mid))
            requeued += 1
    return {"requeued": requeued}


@celery_app.task(name="worker.tasks.whatsapp.retry_pending_messages")
def retry_pending_messages() -> dict[str, object]:
    result: dict[str, object] = asyncio.run(_run_sweep())
    logger.info("Sweep de mensajes WhatsApp pendientes: %s", result)
    return result
