"""Modelos de Créditos, Cuotas, Mora, Autorizaciones y Reservas (#F05-01/02/03).

Convenciones de estado: columnas String + constantes de clase (sin enums de BD),
igual que sales/cash/inventory.

Invariantes financieros clave:
- `CreditInstallment.remaining_amount` es SOLO capital pendiente
  (`amount - paid_amount`, nunca negativo). La mora vive aparte en
  `mora_amount`. Así `MoraService` calcula siempre sobre capital y la mora
  NUNCA se capitaliza sobre mora anterior (#F05-08).
- Deuda total de una cuota = `remaining_amount + mora_amount`.
- Una cuota está PAID cuando `paid_amount >= amount + mora_amount`.
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.customers.domain.models import Customer
    from app.modules.products.domain.models import Product, SerializedUnit
    from app.modules.sales.domain.models import Sale


class AgreementStatus:
    """Estados de CreditAgreement."""

    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    DEFAULTED = "DEFAULTED"
    CANCELLED = "CANCELLED"
    RESTRUCTURED = "RESTRUCTURED"

    ALL = {
        PENDING_APPROVAL,
        APPROVED,
        ACTIVE,
        PAID,
        OVERDUE,
        DEFAULTED,
        CANCELLED,
        RESTRUCTURED,
    }


class InstallmentStatus:
    """Estados de CreditInstallment."""

    PENDING = "PENDING"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    RESTRUCTURED = "RESTRUCTURED"
    CANCELLED = "CANCELLED"

    ALL = {PENDING, PARTIALLY_PAID, PAID, OVERDUE, RESTRUCTURED, CANCELLED}

    UNPAID = {PENDING, PARTIALLY_PAID, OVERDUE}


class AuthorizationType:
    """Tipos de CreditAuthorization (#F05-04)."""

    NEW_CREDIT = "NEW_CREDIT"
    WAIVE_INITIAL = "WAIVE_INITIAL"
    OVERRIDE_LIMIT = "OVERRIDE_LIMIT"
    MULTIPLE_CREDITS = "MULTIPLE_CREDITS"
    OVERRIDE_DELINQUENCY = "OVERRIDE_DELINQUENCY"


class CreditAgreement(BaseModel, Base):
    """Acuerdo de crédito CRD-YYYY-XXXXX (#F05-01)."""

    __tablename__ = "credit_agreements"
    __table_args__ = (
        CheckConstraint(
            "financed_amount = total_amount - initial_payment",
            name="financed_matches_total",
        ),
        CheckConstraint("installment_amount > 0", name="installment_positive"),
        CheckConstraint("initial_payment >= 0", name="initial_non_negative"),
        CheckConstraint("number_of_installments > 0", name="installments_count_positive"),
    )

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AgreementStatus.ACTIVE, index=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    initial_payment: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    financed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    number_of_installments: Mapped[int] = mapped_column(nullable=False)
    installment_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=0)
    interest_free_months: Mapped[int] = mapped_column(nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    exchange_rate_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exchange_rate_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    authorized_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    authorization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("credit_authorizations.id", ondelete="SET NULL"), nullable=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    customer: Mapped[Customer] = relationship("Customer", lazy="selectin")
    sale: Mapped[Sale] = relationship("Sale", lazy="selectin")
    installments: Mapped[list[CreditInstallment]] = relationship(
        "CreditInstallment", back_populates="agreement", lazy="selectin"
    )


class CreditInstallment(BaseModel, Base):
    """Cuota mensual de un acuerdo de crédito (#F05-02).

    `remaining_amount` = capital pendiente (`amount - paid_amount`).
    `mora_amount` acumula mora generada por períodos vencidos.
    """

    __tablename__ = "credit_installments"
    __table_args__ = (
        UniqueConstraint("agreement_id", "number", name="uq_credit_installments_agreement_number"),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("paid_amount >= 0", name="paid_non_negative"),
        CheckConstraint("mora_amount >= 0", name="mora_non_negative"),
    )

    agreement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    number: Mapped[int] = mapped_column(nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    mora_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=InstallmentStatus.PENDING, index=True)
    original_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    restructured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    restructured_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    restructure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    agreement: Mapped[CreditAgreement] = relationship("CreditAgreement", back_populates="installments", lazy="selectin")
    payments: Mapped[list[CreditPayment]] = relationship("CreditPayment", back_populates="installment", lazy="selectin")


class CreditPayment(BaseModel, Base):
    """Pago (total o parcial) aplicado a una cuota (#F05-06)."""

    __tablename__ = "credit_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_credit_payments_agreement_paid", "agreement_id", "paid_at"),
    )

    installment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_installments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    agreement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_agreements.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    method_detail: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cash_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cash_sessions.id", ondelete="RESTRICT"), nullable=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True, index=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registered_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    installment: Mapped[CreditInstallment] = relationship("CreditInstallment", back_populates="payments", lazy="selectin")


class CreditAuthorization(BaseModel, Base):
    """Autorización especial de OWNER para saltar un bloqueo de crédito (#F05-04)."""

    __tablename__ = "credit_authorizations"

    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    requested_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CreditMora(BaseModel, Base):
    """Cargo mensual de mora por cuota vencida (#F05-08).

    UNIQUE (installment_id, period) garantiza idempotencia: nunca doble mora
    en el mismo período. Se calcula siempre sobre el CAPITAL pendiente
    (`principal_vencido`), jamás sobre mora acumulada.
    """

    __tablename__ = "credit_moras"
    __table_args__ = (
        UniqueConstraint("installment_id", "period", name="uq_credit_moras_installment_period"),
        Index("ix_credit_moras_period", "period"),
    )

    installment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_installments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agreement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("credit_agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    principal_vencido: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    mora_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class ReservationStatus:
    """Estados de Reservation."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    CONVERTED_TO_SALE = "CONVERTED_TO_SALE"
    CONVERTED_TO_CREDIT = "CONVERTED_TO_CREDIT"


class Reservation(BaseModel, Base):
    """Reserva de stock para una venta/crédito (#F05-03).

    Al crear: genera InventoryMovement(RESERVATION).
    Al cancelar: InventoryMovement(RELEASE_RESERVATION).
    """

    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("initial_amount >= 0", name="initial_non_negative"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    serialized_unit_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("serialized_units.id", ondelete="SET NULL"), nullable=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sale_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sales.id", ondelete="SET NULL"), nullable=True
    )
    credit_agreement_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("credit_agreements.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=ReservationStatus.ACTIVE, index=True)
    initial_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    product: Mapped[Product] = relationship("Product", lazy="selectin")
    serialized_unit: Mapped[SerializedUnit | None] = relationship("SerializedUnit", lazy="selectin")
