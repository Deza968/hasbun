"""Tareas de salud del worker Celery."""

from __future__ import annotations

from worker.celery_app import celery_app


@celery_app.task(name="worker.tasks.health.ping")
def ping() -> str:
    """Tarea de prueba que verifica que el worker responde."""
    return "pong"