"""Servicio de auditoría transversal.

`log()` nunca lanza excepción: si falla el registro, se loguea al logger
pero no se interrumpe el flujo del negocio.
"""

from __future__ import annotations

import logging
import uuid

from app.modules.audit.domain.models import AuditLog

logger = logging.getLogger("hasbun.audit")


async def log(
    *,
    action: str,
    module: str,
    user_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    old_values: dict | None = None,
    new_values: dict | None = None,
    authorization_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    request_id: uuid.UUID | None = None,
) -> None:
    """Registra una acción de auditoría sin interrumpir el flujo.

    La sesión debe ser gestionada por el llamador (se hace commit de la
    transacción principal o se ejecuta en la misma sesión).
    """
    try:
        from app.database.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            session.add(
                AuditLog(
                    user_id=user_id,
                    action=action,
                    module=module,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    old_values=old_values,
                    new_values=new_values,
                    authorization_id=authorization_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                )
            )
            await session.commit()
    except Exception:  # noqa: BLE001 - la auditoría nunca interrumpe el flujo
        logger.exception("Fallo al registrar auditoría (acción=%s)", action)
