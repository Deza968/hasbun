"""Aplicación Celery para Hasbun.

- Broker y result backend en Redis.
- Beat schedule (tareas reales se agregan en cada fase).
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "hasbun",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "worker.tasks.health",
        "worker.tasks.exchange_rates",
        "worker.tasks.inventory",
        "worker.tasks.mora",
        "worker.tasks.whatsapp",
        "worker.tasks.quotes",
        "worker.tasks.credits",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Lima",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    beat_schedule={
        # Se agregarán tareas por fase: mora, exchange rates, alertas, backups.
        "health-ping-every-minute": {
            "task": "worker.tasks.health.ping",
            "schedule": crontab(minute="*/1"),
        },
        "update-exchange-rates-daily": {
            "task": "worker.tasks.exchange_rates.update_exchange_rates",
            "schedule": crontab(
                minute=0, hour=settings.EXCHANGE_RATE_UPDATE_HOUR
            ),
        },
        "check-low-stock-morning": {
            "task": "worker.tasks.inventory.check_low_stock",
            "schedule": crontab(minute=0, hour=9),
        },
        "check-low-stock-afternoon": {
            "task": "worker.tasks.inventory.check_low_stock",
            "schedule": crontab(minute=0, hour=15),
        },
        "daily-stock-report": {
            "task": "worker.tasks.inventory.generate_daily_stock_report",
            "schedule": crontab(minute=0, hour=8),
        },
        # #F05-09: mora diaria — actúa solo el día 1 de cada mes, 6 AM
        "apply-mora-daily": {
            "task": "worker.tasks.mora.apply_daily_mora",
            "schedule": crontab(minute=0, hour=settings.MORA_APPLY_HOUR),
        },
        # #F06-04: expiración de cotizaciones — diaria 7 AM
        "expire-quotes-daily": {
            "task": "worker.tasks.quotes.expire_pending_quotes",
            "schedule": crontab(minute=0, hour=7),
        },
        # #F06-11: recordatorios de cuotas próximas (hoy + 3 días) — diaria 9 AM
        "installment-reminders-daily": {
            "task": "worker.tasks.credits.send_upcoming_installment_reminders",
            "schedule": crontab(minute=0, hour=9),
        },
        # #F06-09: reintento de mensajes WhatsApp PENDING vencidos — cada 15 min
        "whatsapp-retry-pending": {
            "task": "worker.tasks.whatsapp.retry_pending_messages",
            "schedule": crontab(minute="*/15"),
        },
    },
)