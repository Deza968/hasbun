"""Modelo Customer (#F04-21)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    pass


class Customer(BaseModel, Base):
    __tablename__ = "customers"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="PERSON")
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    razon_social: Mapped[str | None] = mapped_column(String(255), nullable=True)
    dni: Mapped[str | None] = mapped_column(String(8), unique=True, nullable=True)
    ruc: Mapped[str | None] = mapped_column(String(11), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_whatsapp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_frequent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
