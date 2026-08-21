"""Schemas de Créditos y Cuotas (#F05-05/06/07/10/11)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreditItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0)
    serialized_unit_id: uuid.UUID | None = None


class CreditValidateIn(BaseModel):
    """Verificación pre-crédito en tiempo real (frontend #F05-12)."""

    customer_id: uuid.UUID
    total_amount: Decimal = Field(..., gt=0)
    initial_payment: Decimal = Field(default=Decimal("0"), ge=0)
    number_of_installments: int = Field(..., ge=1, le=60)
    authorization_ids: list[uuid.UUID] = Field(default_factory=list)


class CreditSaleCreate(CreditValidateIn):
    items: list[CreditItemCreate] = Field(..., min_length=1)
    interest_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    interest_free_months: int = Field(default=0, ge=0)
    currency: str = "PEN"
    first_due_date: date
    initial_method: str = "CASH"
    cash_session_id: uuid.UUID | None = None
    notes: str | None = None


class BlockerOut(BaseModel):
    type: str
    authorization: str
    message: str


class ValidationResponse(BaseModel):
    approved: bool
    blockers: list[BlockerOut]
    warnings: list[BlockerOut]


class PaymentOut(BaseModel):
    id: uuid.UUID
    installment_id: uuid.UUID
    amount: Decimal
    method: str
    paid_at: datetime
    reference: str | None = None


class InstallmentOut(BaseModel):
    id: uuid.UUID
    agreement_id: uuid.UUID
    number: int
    amount: Decimal
    due_date: date
    original_due_date: date | None
    paid_amount: Decimal
    remaining_amount: Decimal
    mora_amount: Decimal
    total_due: Decimal
    status: str
    restructure_reason: str | None = None

    @classmethod
    def from_model(cls, i) -> InstallmentOut:
        return cls(
            id=i.id,
            agreement_id=i.agreement_id,
            number=i.number,
            amount=i.amount,
            due_date=i.due_date,
            original_due_date=i.original_due_date,
            paid_amount=i.paid_amount,
            remaining_amount=i.remaining_amount,
            mora_amount=i.mora_amount,
            total_due=(i.remaining_amount + i.mora_amount),
            status=i.status,
            restructure_reason=i.restructure_reason,
        )


class InstallmentListResponse(BaseModel):
    items: list[InstallmentOut]
    total: int


class CreditResponse(BaseModel):
    id: uuid.UUID
    code: str
    customer_id: uuid.UUID
    sale_id: uuid.UUID
    status: str
    total_amount: Decimal
    initial_payment: Decimal
    financed_amount: Decimal
    number_of_installments: int
    installment_amount: Decimal
    interest_rate: Decimal
    interest_free_months: int
    currency: str
    exchange_rate: Decimal
    first_due_date: date
    created_at: datetime
    installments: list[InstallmentOut] = []

    @classmethod
    def from_model(cls, a) -> CreditResponse:
        return cls(
            id=a.id,
            code=a.code,
            customer_id=a.customer_id,
            sale_id=a.sale_id,
            status=a.status,
            total_amount=a.total_amount,
            initial_payment=a.initial_payment,
            financed_amount=a.financed_amount,
            number_of_installments=a.number_of_installments,
            installment_amount=a.installment_amount,
            interest_rate=a.interest_rate,
            interest_free_months=a.interest_free_months,
            currency=a.currency,
            exchange_rate=a.exchange_rate,
            first_due_date=a.first_due_date,
            created_at=a.created_at,
            installments=[InstallmentOut.from_model(i) for i in sorted(a.installments, key=lambda x: x.number)],
        )


class CreditSummaryResponse(BaseModel):
    """Crédito resumido para listados."""

    id: uuid.UUID
    code: str
    customer_id: uuid.UUID
    customer_name: str | None = None
    status: str
    total_amount: Decimal
    financed_amount: Decimal
    number_of_installments: int
    paid_installments: int
    overdue_installments: int
    pending_total: Decimal
    created_at: datetime


class CreditListResponse(BaseModel):
    items: list[CreditSummaryResponse]
    total: int


class PayRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    method: str = Field(default="CASH")
    method_detail: str | None = None
    reference: str | None = None
    idempotency_key: str | None = None
    cash_session_id: uuid.UUID | None = None


class PayMultipleRequest(BaseModel):
    installment_ids: list[uuid.UUID] = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    method: str = "CASH"
    reference: str | None = None
    idempotency_key: str | None = None
    cash_session_id: uuid.UUID | None = None


class RestructureRequest(BaseModel):
    new_due_date: date
    reason: str = Field(..., min_length=5)


class DelinquencyRow(BaseModel):
    customer_id: uuid.UUID
    customer_name: str | None
    active_credits: int
    overdue_installments: int
    overdue_capital: Decimal
    mora_total: Decimal
    days_late_max: int


class DelinquencyResponse(BaseModel):
    rows: list[DelinquencyRow]
    mora_system_total: Decimal
    affected_customers: int
