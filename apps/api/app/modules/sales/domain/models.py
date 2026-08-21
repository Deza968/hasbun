"""Modelos Sales y DiscountAuthorization (#F04-06/07)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.customers.domain.models import Customer
    from app.modules.products.domain.models import Product


class DiscountAuthorization(BaseModel, Base):
    __tablename__ = "discount_authorizations"
    __table_args__ = (
        CheckConstraint("percentage >= 0 AND percentage <= 1", name="percentage_range"),
        CheckConstraint("fixed_amount >= 0", name="fixed_amount_positive"),
    )

    sale_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    fixed_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DocumentSequence(Base):
    __tablename__ = "document_sequences"
    prefix: Mapped[str] = mapped_column(String(10), primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    last_value: Mapped[int] = mapped_column(default=0, nullable=False)


class Sale(BaseModel, Base):
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("total >= 0", name="total_non_negative"),
        CheckConstraint("discount_amount >= 0", name="discount_non_negative"),
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    sale_type: Mapped[str] = mapped_column(String(20), nullable=False, default="CASH")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PAID", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=1)
    exchange_rate_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exchange_rate_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discount_authorization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("discount_authorizations.id", ondelete="SET NULL"), nullable=True)
    cash_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    customer: Mapped[Customer | None] = relationship("Customer", lazy="selectin")
    items: Mapped[list[SaleItem]] = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan", lazy="selectin")
    payments: Mapped[list[SalePayment]] = relationship("SalePayment", back_populates="sale", cascade="all, delete-orphan", lazy="selectin")


class SaleItem(BaseModel, Base):
    __tablename__ = "sale_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    serialized_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("serialized_units.id", ondelete="SET NULL"), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    sale: Mapped[Sale] = relationship("Sale", back_populates="items", lazy="selectin")
    product: Mapped[Product] = relationship("Product", lazy="selectin")


class SalePayment(BaseModel, Base):
    __tablename__ = "sale_payments"

    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    method_detail: Mapped[str | None] = mapped_column(String(120), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    sale: Mapped[Sale] = relationship("Sale", back_populates="payments", lazy="selectin")
