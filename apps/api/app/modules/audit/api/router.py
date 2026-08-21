"""Router de auditoría (solo OWNER, solo lectura)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.audit.domain.models import AuditLog
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select

router = APIRouter(tags=["audit"])

ViewAudit = Annotated[User, Depends(require_permission("auditoria.ver"))]


class AuditEntry(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    module: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    ip_address: str | None
    timestamp: datetime


class AuditListResponse(BaseModel):
    items: list[AuditEntry]
    total: int


@router.get("/audit", response_model=AuditListResponse)
async def list_audit(
    db: DbSession,
    _: ViewAudit,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    module: Annotated[str | None, Query()] = None,
    user_id: Annotated[uuid.UUID | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    entity_type: Annotated[str | None, Query()] = None,
    entity_id: Annotated[uuid.UUID | None, Query()] = None,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
) -> AuditListResponse:
    """Lista registros de auditoría con filtros (solo OWNER)."""
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    if module:
        query = query.where(AuditLog.module == module)
        count_query = count_query.where(AuditLog.module == module)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLog.entity_id == entity_id)
        count_query = count_query.where(AuditLog.entity_id == entity_id)
    if from_date:
        query = query.where(AuditLog.timestamp >= from_date)
        count_query = count_query.where(AuditLog.timestamp >= from_date)
    if to_date:
        query = query.where(AuditLog.timestamp <= to_date)
        count_query = count_query.where(AuditLog.timestamp <= to_date)

    total = (await db.execute(count_query)).scalar_one()  # type: ignore[arg-type]
    rows = (
        await db.execute(
            query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        )
    ).scalars().all()
    return AuditListResponse(
        items=[
            AuditEntry(
                id=e.id,
                user_id=e.user_id,
                action=e.action,
                module=e.module,
                entity_type=e.entity_type,
                entity_id=e.entity_id,
                ip_address=e.ip_address,
                timestamp=e.timestamp,
            )
            for e in rows
        ],
        total=total,
    )
