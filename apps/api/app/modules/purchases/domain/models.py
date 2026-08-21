"""Modelos del módulo de compras (#F03-08)."""

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
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.files.domain.models import FileObject
    from app.modules.products.domain.models import Product
    from app.modules.suppliers.domain.models import Supplier
    from app.modules.users.domain.models import User


class PurchaseStatus:
    DRAFT = "DRAFT"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"

    ALL = {DRAFT, ORDERED, RECEIVED, PARTIAL, CANCELLED}


class PurchaseSequence(Base):
    """Secuencia por año para el código transaccional de compras (#F03-09)."""

    __tablename__ = "purchase_sequences"

    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Purchase(BaseModel, Base):
    __tablename__ = "purchases"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    supplier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PurchaseStatus.DRAFT, index=True
    )
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=1)
    exchange_rate_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_file_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("file_objects.id", ondelete="SET NULL"), nullable=True
    )
    received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    supplier: Mapped[Supplier] = relationship("Supplier", lazy="selectin")
    items: Mapped[list[PurchaseItem]] = relationship(
        "PurchaseItem",
        back_populates="purchase",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    creator: Mapped[User | None] = relationship("User", lazy="selectin")
    invoice_file: Mapped[FileObject | None] = relationship("FileObject", lazy="selectin")


class PurchaseItem(BaseModel, Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="unit_cost_non_negative"),
    )

    purchase_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("purchases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=0
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    purchase: Mapped[Purchase] = relationship(
        "Purchase", back_populates="items", lazy="selectin"
    )
    product: Mapped[Product] = relationship("Product", lazy="selectin")
