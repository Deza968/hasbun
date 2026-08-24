"""Servicio de notificaciones internas (#F06-14).

Distribución por rol (REQUIREMENTS §24.2): `notify_roles` crea una
notificación por cada usuario ACTIVO de los roles indicados.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import AuthorizationError, NotFoundError
from app.modules.notifications.domain.models import Notification
from app.modules.roles.domain.models import Role
from app.modules.users.domain.models import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    type_: str,
    title: str,
    message: str,
    priority: str = "MEDIUM",
    related_type: str | None = None,
    related_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        type=type_,
        title=title[:200],
        message=message,
        priority=priority,
        related_type=related_type,
        related_id=related_id,
    )
    db.add(notification)
    await db.flush()
    return notification


async def notify_roles(
    db: AsyncSession,
    *,
    role_codes: list[str],
    type_: str,
    title: str,
    message: str,
    priority: str = "MEDIUM",
    related_type: str | None = None,
    related_id: uuid.UUID | None = None,
) -> list[Notification]:
    """Crea una notificación por cada usuario activo de los roles dados."""
    users = (
        await db.execute(
            select(User)
            .join(User.roles)
            .where(Role.code.in_(role_codes), User.is_active.is_(True))
            .distinct()
        )
    ).scalars().all()
    created = []
    for u in users:
        created.append(
            await create_notification(
                db,
                user_id=u.id,
                type_=type_,
                title=title,
                message=message,
                priority=priority,
                related_type=related_type,
                related_id=related_id,
            )
        )
    return created


async def list_notifications(
    db: AsyncSession, *, user_id: uuid.UUID, unread_only: bool = False, page: int = 1, per_page: int = 20
) -> tuple[list[Notification], int]:
    q = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        q = q.where(Notification.read.is_(False))
    total = (
        await db.execute(select(func.count()).select_from(q.order_by(None).subquery()))
    ).scalar_one()
    rows = await db.execute(
        q.order_by(Notification.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    return list(rows.scalars().all()), int(total)


async def mark_read(db: AsyncSession, *, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
    """Marca leída SOLO si pertenece al usuario (si no → 403)."""
    notification = await db.get(Notification, notification_id)
    if notification is None:
        raise NotFoundError("Notificación no encontrada")
    if notification.user_id != user_id:
        raise AuthorizationError("No puedes modificar notificaciones de otro usuario")
    if not notification.read:
        notification.read = True
        notification.read_at = datetime.now(UTC)
        await db.commit()
    return notification


async def mark_all_read(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    rows = (
        await db.execute(select(Notification).where(Notification.user_id == user_id, Notification.read.is_(False)))
    ).scalars().all()
    now = datetime.now(UTC)
    for n in rows:
        n.read = True
        n.read_at = now
    await db.commit()
    return len(rows)


async def unread_count(db: AsyncSession, *, user_id: uuid.UUID) -> int:
    total = (
        await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read.is_(False))
        )
    ).scalar_one()
    return int(total)


__all__ = ["Any"]
