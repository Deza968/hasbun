"""Modelo de tipo de cambio (#F02-01)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.database.base import Base, BaseModel
from sqlalchemy import DateTime, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column


class ExchangeRate(BaseModel, Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (
        Index(
            "ix_exchange_rates_pair_effective",
            "currency_from",
            "currency_to",
            "effective_at",
        ),
    )

    currency_from: Mapped[str] = mapped_column(String(3), nullable=False)
    currency_to: Mapped[str] = mapped_column(String(3), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
