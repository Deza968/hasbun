"""Schemas del módulo de caja (#F04-02/03/04/05)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.modules.cash.domain.models import (
    CashClosureRequest,
    CashMovement,
    CashRegister,
    CashSession,
)
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Registers
# ---------------------------------------------------------------------------


class CashRegisterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    user_id: uuid.UUID | None = None
    is_general: bool = False


class CashRegisterResponse(BaseModel):
    id: uuid.UUID
    name: str
    user_id: uuid.UUID | None
    is_general: bool
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, register: CashRegister) -> CashRegisterResponse:
        return cls(
            id=register.id,
            name=register.name,
            user_id=register.user_id,
            is_general=register.is_general,
            active=register.active,
            created_at=register.created_at,
            updated_at=register.updated_at,
        )


class CashRegisterListResponse(BaseModel):
    items: list[CashRegisterResponse]
    total: int


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class OpenSessionRequest(BaseModel):
    register_id: uuid.UUID
    opening_amount: Decimal = Field(..., ge=0)

    @field_validator("opening_amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class CloseSessionRequest(BaseModel):
    counted_cash: Decimal = Field(..., ge=0)

    @field_validator("counted_cash")
    @classmethod
    def validate_counted(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class SessionResponse(BaseModel):
    id: uuid.UUID
    register_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    opening_amount: Decimal
    expected_cash: Decimal
    counted_cash: Decimal
    difference: Decimal
    opened_at: datetime | None
    closed_at: datetime | None
    opened_by: uuid.UUID | None
    closed_by: uuid.UUID | None
    balance: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(
        cls, session: CashSession, balance: Decimal | None = None
    ) -> SessionResponse:
        return cls(
            id=session.id,
            register_id=session.register_id,
            user_id=session.user_id,
            status=session.status,
            opening_amount=session.opening_amount,
            expected_cash=session.expected_cash,
            counted_cash=session.counted_cash,
            difference=session.difference,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
            opened_by=session.opened_by,
            closed_by=session.closed_by,
            balance=balance,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int


# ---------------------------------------------------------------------------
# Movements
# ---------------------------------------------------------------------------


class MovementCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=500)
    reference_type: str | None = Field(default=None, max_length=40)
    reference_id: uuid.UUID | None = None
    idempotency_key: str | None = Field(default=None, max_length=80)
    type: str | None = Field(default=None, max_length=40)
    direction: str | None = Field(default=None, max_length=10)


class IncomeRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=80)
    reference_type: str | None = Field(default=None, max_length=40)
    reference_id: uuid.UUID | None = None


class ExpenseRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=80)
    reference_type: str | None = Field(default=None, max_length=40)
    reference_id: uuid.UUID | None = None


class MovementResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    type: str
    amount: Decimal
    direction: str
    reference_type: str | None
    reference_id: uuid.UUID | None
    reason: str | None
    authorized_by: uuid.UUID | None
    idempotency_key: str | None
    created_by: uuid.UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, m: CashMovement) -> MovementResponse:
        return cls(
            id=m.id,
            session_id=m.session_id,
            type=m.type,
            amount=m.amount,
            direction=m.direction,
            reference_type=m.reference_type,
            reference_id=m.reference_id,
            reason=m.reason,
            authorized_by=m.authorized_by,
            idempotency_key=m.idempotency_key,
            created_by=m.created_by,
            created_at=m.created_at,
        )


class MovementListResponse(BaseModel):
    items: list[MovementResponse]
    total: int


# ---------------------------------------------------------------------------
# Transfers
# ---------------------------------------------------------------------------


class TransferRequest(BaseModel):
    from_session_id: uuid.UUID
    to_session_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=80)


class TransferResponse(BaseModel):
    id: uuid.UUID
    from_session_id: uuid.UUID
    to_session_id: uuid.UUID
    amount: Decimal
    reason: str | None
    out_movement_id: uuid.UUID | None
    in_movement_id: uuid.UUID | None
    created_by: uuid.UUID | None
    created_at: datetime

    @classmethod
    def from_model(cls, t) -> TransferResponse:
        return cls(
            id=t.id,
            from_session_id=t.from_session_id,
            to_session_id=t.to_session_id,
            amount=t.amount,
            reason=t.reason,
            out_movement_id=t.out_movement_id,
            in_movement_id=t.in_movement_id,
            created_by=t.created_by,
            created_at=t.created_at,
        )


# ---------------------------------------------------------------------------
# Closure requests
# ---------------------------------------------------------------------------


class ClosureRequestResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    expected_cash: Decimal
    counted_cash: Decimal
    difference: Decimal
    status: str
    requested_by: uuid.UUID | None
    reviewed_by: uuid.UUID | None
    review_reason: str | None
    requested_at: datetime
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, r: CashClosureRequest) -> ClosureRequestResponse:
        return cls(
            id=r.id,
            session_id=r.session_id,
            expected_cash=r.expected_cash,
            counted_cash=r.counted_cash,
            difference=r.difference,
            status=r.status,
            requested_by=r.requested_by,
            reviewed_by=r.reviewed_by,
            review_reason=r.review_reason,
            requested_at=r.requested_at,
            reviewed_at=r.reviewed_at,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )


class ClosureRequestListResponse(BaseModel):
    items: list[ClosureRequestResponse]
    total: int


class ReviewClosureRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)
