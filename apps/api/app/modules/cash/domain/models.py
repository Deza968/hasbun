"""Modelos de Caja (#F04-01)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.users.domain.models import User


class CashRegister(BaseModel, Base):
    __tablename__ = "cash_registers"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_general: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner: Mapped[User | None] = relationship("User", lazy="selectin")


class CashSession(BaseModel, Base):
    __tablename__ = "cash_sessions"
    __table_args__ = (
        Index(
            "ix_cash_sessions_user_open",
            "user_id",
            "status",
            unique=True,
            postgresql_where=text("status = 'OPEN'"),
        ),
        CheckConstraint(
            "difference = counted_cash - expected_cash",
            name="difference_check",
        ),
    )

    register_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cash_registers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)
    opening_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    expected_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    counted_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    difference: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    register: Mapped[CashRegister] = relationship("CashRegister", lazy="selectin")
    opener: Mapped[User | None] = relationship("User", foreign_keys=[opened_by], lazy="selectin")


class CashMovement(BaseModel, Base):
    __tablename__ = "cash_movements"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_cash_movements_idempotency"),
        CheckConstraint("amount > 0", name="amount_positive"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    authorized_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    session: Mapped[CashSession] = relationship("CashSession", lazy="selectin")


class CashTransfer(BaseModel, Base):
    __tablename__ = "cash_transfers"

    from_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    to_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    out_movement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cash_movements.id", ondelete="SET NULL"), nullable=True
    )
    in_movement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cash_movements.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class CashClosureRequest(BaseModel, Base):
    __tablename__ = "cash_closure_requests"

    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expected_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    counted_cash: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped[CashSession] = relationship("CashSession", lazy="selectin")
