"""Tarea Celery de mora mensual automática (#F05-09).

Se ejecuta diariamente a las 6 AM (America/Lima). Solo actúa el primer día
del mes, aplicando la mora del período actual a las cuotas vencidas.
Es idempotente: UNIQUE (installment_id, period) + verificación previa evitan
doble mora aunque la tarea se ejecute varias veces el mismo día.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date

from worker.celery_app import celery_app

logger = logging.getLogger("hasbun.worker.mora")


async def _run_mora(period: str) -> dict[str, object]:
    from app.database.session import AsyncSessionLocal
    from app.modules.credits.application.service import apply_mora_for_period

    async with AsyncSessionLocal() as db:
        return await apply_mora_for_period(db, period=period, generated_by="celery-daily")


@celery_app.task(name="worker.tasks.mora.apply_daily_mora", bind=True, max_retries=3)
def apply_daily_mora(self) -> dict[str, object]:  # noqa: ANN001
    """Verifica si es día 1 y aplica mora del período. Idempotente."""
    today = date.today()
    if today.day != 1:
        return {"skipped": True, "reason": "not_first_day_of_month", "date": today.isoformat()}
    try:
        result: dict[str, object] = asyncio.run(
            _run_mora(f"{today.year:04d}-{today.month:02d}")
        )
        logger.info("Mora diaria aplicada: %s", result)
        return result
    except Exception as exc:  # noqa: BLE001 - reintenta y notifica
        logger.exception("Fallo aplicando mora diaria")
        try:
            raise self.retry(exc=exc, countdown=600)  # 10 min entre reintentos
        except Exception:  # noqa: BLE001 - agotados los reintentos
            _notify_failure()
            raise


def _notify_failure() -> None:
    """Placeholder de notificación al OWNER (módulo notifications llega en F12)."""
    logger.critical("apply_daily_mora agotó reintentos — requiere intervención OWNER")
