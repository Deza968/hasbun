"""Modelo de notificaciones internas (#F06-14).

Cada rol recibe solo las relevantes (REQUIREMENTS §24.2): la distribución
se resuelve en `NotificationService.notify_roles`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from app.database.base import Base, BaseModel
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column


class NotificationPriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

    ALL = {LOW, MEDIUM, HIGH, URGENT}


class Notification(BaseModel, Base):
    """Notificación interna dirigida a un usuario."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "read"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default=NotificationPriority.MEDIUM)
    related_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
