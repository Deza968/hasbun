"""Router de cotizaciones (#F06-02/#F06-03)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from app.core.dependencies import DbSession, get_current_active_user, require_permission
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.modules.customers.domain.models import Customer
from app.modules.quotes.application import service
from app.modules.quotes.application.schemas import (
    ConvertQuoteRequest,
    PublicQuoteItem,
    PublicQuoteResponse,
    PublicRespondRequest,
    QuoteCreate,
    QuoteListResponse,
    QuoteResponse,
    QuoteSummary,
    QuoteUpdate,
)
from app.modules.quotes.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select

router = APIRouter(tags=["quotes"])

ViewQuotes = Annotated[User, Depends(require_permission("cotizaciones.ver"))]
CreateQuotes = Annotated[User, Depends(require_permission("cotizaciones.crear"))]
AnyUser = Annotated[User, Depends(get_current_active_user)]


class RejectBody(BaseModel):
    reason: str | None = None


def _customer_name(customer: Customer | None) -> str | None:
    if customer is None:
        return None
    return (
        customer.razon_social
        or " ".join(filter(None, [customer.first_name, customer.last_name]))
        or None
    )


def _public_response(quote) -> PublicQuoteResponse:
    return PublicQuoteResponse(
        code=quote.code,
        status=quote.status,
        customer_name=_customer_name(quote.customer),
        total=quote.total,
        currency=quote.currency,
        valid_until=quote.valid_until,
        notes=quote.notes,
        items=[
            PublicQuoteItem(
                product_name=(i.product.name if i.product else None),
                quantity=i.quantity,
                unit_price=i.unit_price,
                subtotal=i.subtotal,
            )
            for i in quote.items
        ],
    )


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
async def create_quote(body: QuoteCreate, db: DbSession, actor: CreateQuotes):
    """Crear cotización DRAFT — OWNER y SALES (#F06-02)."""
    quote = await service.create_quote(db, data=body, user=actor)
    return QuoteResponse.from_model(quote)


@router.get("/quotes", response_model=QuoteListResponse)
async def list_quotes(
    db: DbSession,
    _: ViewQuotes,
    status: str | None = Query(None),
    customer_id: uuid.UUID | None = Query(None),
    created_by: uuid.UUID | None = Query(None),
    valid_from: date | None = Query(None),
    valid_to: date | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    quotes, total = await repository.list_quotes(
        db,
        status=status,
        customer_id=customer_id,
        created_by=created_by,
        valid_until_from=valid_from,
        valid_until_to=valid_to,
        search=search,
        page=page,
        per_page=per_page,
    )
    items = [
        QuoteSummary(
            id=q.id,
            code=q.code,
            customer_id=q.customer_id,
            customer_name=_customer_name(q.customer),
            status=q.status,
            total=q.total,
            currency=q.currency,
            valid_until=q.valid_until,
            sent_via_whatsapp=q.sent_via_whatsapp,
            created_at=q.created_at,
        )
        for q in quotes
    ]
    return QuoteListResponse(items=items, total=total)


@router.get("/quotes/my", response_model=list[QuoteSummary])
async def my_quotes(db: DbSession, actor: AnyUser):
    """Portal del cliente: cotizaciones vinculadas a su usuario (#F06-06)."""
    row = (await db.execute(select(Customer).where(Customer.user_id == actor.id))).scalars().first()
    if row is None:
        return []
    quotes, _total = await repository.list_quotes(db, customer_id=row.id, per_page=100)
    return [
        QuoteSummary(
            id=q.id,
            code=q.code,
            customer_id=q.customer_id,
            status=q.status,
            total=q.total,
            currency=q.currency,
            valid_until=q.valid_until,
            sent_via_whatsapp=q.sent_via_whatsapp,
            created_at=q.created_at,
        )
        for q in quotes
    ]


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(quote_id: uuid.UUID, db: DbSession, _: ViewQuotes):
    quote = await repository.get_quote(db, quote_id)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    return QuoteResponse.from_model(quote)


@router.put("/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(quote_id: uuid.UUID, body: QuoteUpdate, db: DbSession, actor: CreateQuotes):
    """Editar solo si DRAFT (#F06-02)."""
    quote = await service.update_quote(db, quote_id=quote_id, data=body, user=actor)
    return QuoteResponse.from_model(quote)


@router.post("/quotes/{quote_id}/send", response_model=QuoteResponse)
async def send_quote(quote_id: uuid.UUID, db: DbSession, actor: CreateQuotes):
    quote = await service.send_quote(db, quote_id=quote_id, user=actor)
    return QuoteResponse.from_model(quote)


@router.post("/quotes/{quote_id}/accept", response_model=QuoteResponse)
async def accept_quote(quote_id: uuid.UUID, db: DbSession, actor: AnyUser):
    """Marcar aceptada — admin o portal del cliente."""
    quote = await service.accept_quote(db, quote_id=quote_id, actor=actor)
    return QuoteResponse.from_model(quote)


@router.post("/quotes/{quote_id}/reject", response_model=QuoteResponse)
async def reject_quote(quote_id: uuid.UUID, body: RejectBody, db: DbSession, actor: AnyUser):
    quote = await service.reject_quote(db, quote_id=quote_id, reason=body.reason, actor=actor)
    return QuoteResponse.from_model(quote)


@router.post("/quotes/{quote_id}/convert", response_model=dict)
async def convert_quote(quote_id: uuid.UUID, body: ConvertQuoteRequest, db: DbSession, actor: CreateQuotes):
    """Conversión ATÓMICA a venta contado/crédito sin reingreso de datos (#F06-03).

    CASH exige además `ventas.crear`; CREDIT pasa por las reglas de FASE 05.
    """
    if body.sale_type == "CASH" and not any(
        p.codename == "ventas.crear" for r in actor.roles for p in r.permissions
    ):
        raise AuthorizationError("Se requiere permiso ventas.crear para convertir a contado")
    sale = await service.convert_quote_to_sale(db, quote_id=quote_id, data=body, user=actor)
    return {
        "sale_id": str(sale.id),
        "sale_code": sale.code,
        "sale_status": sale.status,
        "sale_total": str(sale.total),
    }


# ---------------------------------------------------------------------------
# Rutas públicas SIN login (#F06-05): ver y responder desde el link
# ---------------------------------------------------------------------------


@router.get("/quotes/{code}/public", response_model=PublicQuoteResponse)
async def public_quote(code: str, db: DbSession):
    """Vista pública por código. Si estaba SENT pasa a VIEWED automáticamente."""
    quote = await service.public_get_by_code(db, code=code)
    return _public_response(quote)


@router.post("/quotes/{code}/public/respond", response_model=PublicQuoteResponse)
async def public_respond(code: str, body: PublicRespondRequest, db: DbSession):
    """El cliente Acepta/Rechaza desde el link público, sin cuenta."""
    if body.decision not in ("accept", "reject"):
        raise ValidationError("decision debe ser 'accept' o 'reject'")
    quote = await repository.get_by_code(db, code)
    if quote is None:
        raise NotFoundError("Cotización no encontrada")
    if body.decision == "accept":
        quote = await service.accept_quote(db, quote_id=quote.id, actor=None)
    else:
        quote = await service.reject_quote(db, quote_id=quote.id, reason=body.reason, actor=None)
    return _public_response(quote)
