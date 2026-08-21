"""Modelos crédito (#F05-01/02/03)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from app.database.base import Base, BaseModel
from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship


class CreditAgreement(BaseModel, Base):
    __tablename__ = "credit_agreements"
    __table_args__ = (
        CheckConstraint("financed_amount = total_amount - initial_payment", name="financed_check"),
        CheckConstraint("installment_amount > 0", name="installment_positive"),
        CheckConstraint("initial_payment >= 0", name="initial_non_negative"),
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    sale_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    initial_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    financed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    number_of_installments: Mapped[int] = mapped_column(nullable=False)
    installment_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0300"))
    interest_free_months: Mapped[int] = mapped_column(default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False, default=1)
    exchange_rate_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exchange_rate_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    authorized_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    authorization_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("credit_authorizations.id", ondelete="SET NULL"), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class CreditInstallment(BaseModel, Base):
    __tablename__ = "credit_installments"
    agreement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("credit_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    number: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mora_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    original_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    restructured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    restructured_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    restructure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class CreditPayment(BaseModel, Base):
    __tablename__ = "credit_payments"
    installment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("credit_installments.id", ondelete="CASCADE"), nullable=False, index=True)
    agreement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("credit_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    method_detail: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cash_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cash_sessions.id", ondelete="SET NULL"), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), unique=True, nullable=True, index=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registered_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class CreditAuthorization(BaseModel, Base):
    __tablename__ = "credit_authorizations"
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CreditMora(BaseModel, Base):
    __tablename__ = "credit_moras"
    __table_args__ = (UniqueConstraint("installment_id", "period", name="uq_mora_installment_period"),)
    installment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("credit_installments.id", ondelete="CASCADE"), nullable=False, index=True)
    agreement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("credit_agreements.id", ondelete="CASCADE"), nullable=False, index=True)
    principal_vencido: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    mora_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")


class Reservation(BaseModel, Base):
    __tablename__ = "reservations"
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    serialized_unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("serialized_units.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    sale_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("sales.id", ondelete="SET NULL"), nullable=True)
    credit_agreement_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("credit_agreements.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ACTIVE", index=True)
    initial_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
