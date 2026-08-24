"""Router de notificaciones internas (#F06-14)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated

from app.core.dependencies import DbSession, get_current_active_user
from app.modules.notifications.application import service
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/notifications", tags=["notifications"])

AnyUser = Annotated[User, Depends(get_current_active_user)]


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    message: str
    read: bool
    priority: str
    related_type: str | None = None
    related_id: uuid.UUID | None = None
    created_at: datetime
    read_at: datetime | None = None


class NotificationListResponse(BaseModel):
    items: list[NotificationOut]
    total: int
    unread: int


@router.get("", response_model=NotificationListResponse)
async def my_notifications(
    db: DbSession,
    actor: AnyUser,
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    items, total = await service.list_notifications(
        db, user_id=actor.id, unread_only=unread_only, page=page, per_page=per_page
    )
    unread = await service.unread_count(db, user_id=actor.id)
    return NotificationListResponse(
        items=[NotificationOut.model_validate(n) for n in items], total=total, unread=unread
    )


@router.get("/unread-count", response_model=dict)
async def unread_count_endpoint(db: DbSession, actor: AnyUser):
    """Contador para el badge del header (polling cada 30s desde frontend)."""
    return {"unread": await service.unread_count(db, user_id=actor.id)}


@router.post("/read-all", response_model=dict)
async def read_all(db: DbSession, actor: AnyUser):
    count = await service.mark_all_read(db, user_id=actor.id)
    return {"marked": count}


@router.post("/{notification_id}/read", response_model=NotificationOut)
async def mark_one_read(notification_id: uuid.UUID, db: DbSession, actor: AnyUser):
    notification = await service.mark_read(db, notification_id=notification_id, user_id=actor.id)
    return NotificationOut.model_validate(notification)
