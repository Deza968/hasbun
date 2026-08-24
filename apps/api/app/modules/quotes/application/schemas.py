"""Schemas Pydantic de cotizaciones (#F06-02)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class QuoteItemIn(BaseModel):
    product_id: uuid.UUID
    serialized_unit_id: uuid.UUID | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal | None = Field(default=None, ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = None


class QuoteCreate(BaseModel):
    customer_id: uuid.UUID
    items: list[QuoteItemIn] = Field(min_length=1)
    valid_until: date
    currency: str = "PEN"
    notes: str | None = None


class QuoteUpdate(BaseModel):
    items: list[QuoteItemIn] | None = None
    valid_until: date | None = None
    notes: str | None = None


class QuoteItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str | None = None
    product_sku: str | None = None
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    subtotal: Decimal
    notes: str | None = None

    @classmethod
    def from_model(cls, item) -> QuoteItemOut:
        return cls(
            id=item.id,
            product_id=item.product_id,
            product_name=item.product.name if item.product else None,
            product_sku=item.product.sku if item.product else None,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount_amount=item.discount_amount,
            subtotal=item.subtotal,
            notes=item.notes,
        )


class QuoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    customer_id: uuid.UUID
    customer_name: str | None = None
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    exchange_rate: Decimal
    valid_until: date
    notes: str | None = None
    converted_to_sale_id: uuid.UUID | None = None
    sent_via_whatsapp: bool
    viewed_at: datetime | None = None
    responded_at: datetime | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    items: list[QuoteItemOut] = []

    @classmethod
    def from_model(cls, quote) -> QuoteResponse:
        customer = quote.customer
        name = None
        if customer is not None:
            name = (
                customer.razon_social
                or " ".join(filter(None, [customer.first_name, customer.last_name]))
                or None
            )
        return cls(
            id=quote.id,
            code=quote.code,
            customer_id=quote.customer_id,
            customer_name=name,
            status=quote.status,
            subtotal=quote.subtotal,
            discount_amount=quote.discount_amount,
            total=quote.total,
            currency=quote.currency,
            exchange_rate=quote.exchange_rate,
            valid_until=quote.valid_until,
            notes=quote.notes,
            converted_to_sale_id=quote.converted_to_sale_id,
            sent_via_whatsapp=quote.sent_via_whatsapp,
            viewed_at=quote.viewed_at,
            responded_at=quote.responded_at,
            created_by=quote.created_by,
            created_at=quote.created_at,
            items=[QuoteItemOut.from_model(i) for i in quote.items],
        )


class QuoteSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    customer_id: uuid.UUID
    customer_name: str | None = None
    status: str
    total: Decimal
    currency: str
    valid_until: date
    sent_via_whatsapp: bool
    created_at: datetime


class QuoteListResponse(BaseModel):
    items: list[QuoteSummary]
    total: int


class PublicQuoteItem(BaseModel):
    product_name: str | None = None
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal


class PublicQuoteResponse(BaseModel):
    code: str
    status: str
    customer_name: str | None = None
    total: Decimal
    currency: str
    valid_until: date
    notes: str | None = None
    items: list[PublicQuoteItem]


class PublicRespondRequest(BaseModel):
    decision: str  # "accept" | "reject"
    reason: str | None = None


class ConvertQuoteRequest(BaseModel):
    sale_type: str = Field(pattern="^(CASH|CREDIT)$")
    # CASH
    cash_session_id: uuid.UUID | None = None
    payments: list[dict] | None = None
    # CREDIT
    initial_payment: Decimal = Field(default=Decimal("0"), ge=0)
    initial_method: str = "CASH"
    number_of_installments: int = Field(default=1, ge=1)
    interest_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1)
    interest_free_months: int = Field(default=0, ge=0)
    first_due_date: date | None = None
    authorization_ids: list[uuid.UUID] = []
