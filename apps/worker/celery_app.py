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
    include=["worker.tasks.health", "worker.tasks.exchange_rates"],
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
            "schedule": crontab(hour=9, minute=0),
        },
    },
)