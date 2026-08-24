"""Modelos de WhatsApp: templates, mensajes y log de entregas (#F06-07).

El módulo está desacoplado del proveedor: la app solo conoce la interfaz
`WhatsAppProvider` (infrastructure/provider.py). Los envíos son SIEMPRE
asíncronos vía Celery (#F06-09).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.database.base import Base, BaseModel
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    pass


class WhatsAppEventType:
    """Eventos que disparan mensajes (REQUIREMENTS §23.3)."""

    NEW_SALE = "NEW_SALE"
    PAYMENT_RECEIVED = "PAYMENT_RECEIVED"
    INSTALLMENT_UPCOMING = "INSTALLMENT_UPCOMING"
    INSTALLMENT_OVERDUE = "INSTALLMENT_OVERDUE"
    MORA_CREATED = "MORA_CREATED"
    REPAIR_CREATED = "REPAIR_CREATED"
    REPAIR_READY = "REPAIR_READY"
    QUOTE_CREATED = "QUOTE_CREATED"
    QUOTE_ACCEPTED = "QUOTE_ACCEPTED"
    INSTALLATION_CREATED = "INSTALLATION_CREATED"
    INSTALLATION_UPCOMING = "INSTALLATION_UPCOMING"
    STOCK_LOW = "STOCK_LOW"
    STOCK_OUT = "STOCK_OUT"
    WARRANTY_EXPIRING = "WARRANTY_EXPIRING"
    SALE_COMPLETED = "SALE_COMPLETED"

    ALL = {
        NEW_SALE, PAYMENT_RECEIVED, INSTALLMENT_UPCOMING, INSTALLMENT_OVERDUE,
        MORA_CREATED, REPAIR_CREATED, REPAIR_READY, QUOTE_CREATED,
        QUOTE_ACCEPTED, INSTALLATION_CREATED, INSTALLATION_UPCOMING,
        STOCK_LOW, STOCK_OUT, WARRANTY_EXPIRING, SALE_COMPLETED,
    }


class WhatsAppMessageStatus:
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"

    ALL = {PENDING, SENT, DELIVERED, FAILED}


class WhatsAppTemplate(BaseModel, Base):
    """Plantilla con variables `{variable}` editable por OWNER (#F06-12)."""

    __tablename__ = "whatsapp_templates"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    messages: Mapped[list[WhatsAppMessage]] = relationship("WhatsAppMessage", lazy="noload")


class WhatsAppMessage(BaseModel, Base):
    """Mensaje encolado/procesado. Idempotencia por `idempotency_key` única."""

    __tablename__ = "whatsapp_messages"
    __table_args__ = (
        Index("ix_whatsapp_messages_status_created", "status", "created_at"),
    )

    recipient: Mapped[str] = mapped_column(String(50), nullable=False)
    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("whatsapp_templates.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WhatsAppMessageStatus.PENDING, index=True
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    provider_message_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    template: Mapped[WhatsAppTemplate] = relationship("WhatsAppTemplate", lazy="selectin", overlaps="messages")
    delivery_logs: Mapped[list[WhatsAppDeliveryLog]] = relationship(
        "WhatsAppDeliveryLog", back_populates="message", lazy="selectin"
    )


class WhatsAppDeliveryLog(BaseModel, Base):
    """Registro de cada intento de envío (éxito o fallo)."""

    __tablename__ = "whatsapp_delivery_logs"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("whatsapp_messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_response: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    message: Mapped[WhatsAppMessage] = relationship(
        "WhatsAppMessage", back_populates="delivery_logs", lazy="selectin"
    )


class WhatsAppConfig(BaseModel, Base):
    """Configuración global del módulo (una sola fila): switch on/off + proveedor."""

    __tablename__ = "whatsapp_config"

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    provider: Mapped[str] = mapped_column(String(30), nullable=False, default="mock")
