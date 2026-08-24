"""Modelos de Cotizaciones (#F06-01).

Convención de estados: columnas String + constantes de clase (sin enums de BD),
igual que sales/credits/cash.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.customers.domain.models import Customer
    from app.modules.products.domain.models import Product
    from app.modules.sales.domain.models import Sale
    from app.modules.users.domain.models import User


class QuoteStatus:
    """Estados de Quote (#F06-01 / REQUIREMENTS §14.2)."""

    DRAFT = "DRAFT"
    SENT = "SENT"
    VIEWED = "VIEWED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"

    ALL = {DRAFT, SENT, VIEWED, ACCEPTED, REJECTED, EXPIRED, CONVERTED}

    # estados que la tarea Celery puede expirar (#F06-04)
    EXPIRABLE = {DRAFT, SENT, VIEWED}
    # estados en los que el cliente aún puede responder
    RESPONDABLE = {SENT, VIEWED}


class Quote(BaseModel, Base):
    """Cotización COT-YYYY-XXXXX (#F06-01).

    Los precios se congelan al crear: si cambian después, la cotización
    NO se actualiza automáticamente (REQUIREMENTS §14.3).
    """

    __tablename__ = "quotes"
    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="subtotal_non_negative"),
        CheckConstraint("discount_amount >= 0", name="discount_non_negative"),
        CheckConstraint("total >= 0", name="total_non_negative"),
        Index("ix_quotes_status_created", "status", "created_at"),
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=QuoteStatus.DRAFT, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=1)
    exchange_rate_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exchange_rate_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    converted_to_sale_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"), nullable=True
    )
    sent_via_whatsapp: Mapped[bool] = mapped_column(nullable=False, default=False)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    customer: Mapped[Customer] = relationship("Customer", lazy="selectin")
    sale: Mapped[Sale | None] = relationship("Sale", lazy="selectin")
    items: Mapped[list[QuoteItem]] = relationship(
        "QuoteItem", back_populates="quote", lazy="selectin", cascade="all, delete-orphan"
    )


class QuoteItem(BaseModel, Base):
    """Ítem de cotización con precio congelado (#F06-01)."""

    __tablename__ = "quote_items"

    quote_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    quote: Mapped[Quote] = relationship("Quote", back_populates="items", lazy="selectin")
    product: Mapped[Product] = relationship("Product", lazy="selectin")


__all__ = ["Quote", "QuoteItem", "QuoteStatus", "User"]
