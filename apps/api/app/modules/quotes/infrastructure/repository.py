"""Repositorio de cotizaciones (#F06-01/#F06-02)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from app.modules.quotes.domain.models import Quote, QuoteItem, QuoteStatus
from app.modules.sales.domain.models import DocumentSequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Carga ansiosa de relaciones usadas por los schemas (evita MissingGreenlet)
_QUOTE_LOAD = (
    selectinload(Quote.customer),
    selectinload(Quote.items).selectinload(QuoteItem.product),
)


async def next_quote_code(db: AsyncSession) -> str:
    """COT-YYYY-XXXXX transaccional (SELECT FOR UPDATE sobre document_sequences)."""
    from datetime import datetime as dt

    year = dt.now(UTC).year
    row = (
        await db.execute(
            select(DocumentSequence)
            .where(DocumentSequence.prefix == "COT", DocumentSequence.year == year)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        row = DocumentSequence(prefix="COT", year=year, last_value=1)
        db.add(row)
        await db.flush()
        return f"COT-{year}-{1:05d}"
    row.last_value += 1
    await db.flush()
    return f"COT-{year}-{row.last_value:05d}"


async def get_quote(db: AsyncSession, quote_id: uuid.UUID) -> Quote | None:
    row = await db.execute(select(Quote).options(*_QUOTE_LOAD).where(Quote.id == quote_id))
    return row.scalars().first()


async def get_by_code(db: AsyncSession, code: str) -> Quote | None:
    row = await db.execute(select(Quote).options(*_QUOTE_LOAD).where(Quote.code == code))
    return row.scalars().first()


async def list_quotes(
    db: AsyncSession,
    *,
    status: str | None = None,
    customer_id: uuid.UUID | None = None,
    created_by: uuid.UUID | None = None,
    valid_until_from: date | None = None,
    valid_until_to: date | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Quote], int]:
    q = select(Quote)
    if status:
        q = q.where(Quote.status == status)
    if customer_id:
        q = q.where(Quote.customer_id == customer_id)
    if created_by:
        q = q.where(Quote.created_by == created_by)
    if valid_until_from:
        q = q.where(Quote.valid_until >= valid_until_from)
    if valid_until_to:
        q = q.where(Quote.valid_until <= valid_until_to)
    if search:
        like = f"%{search}%"
        q = q.join(Quote.customer).where(
            (Quote.code.ilike(like))
            | (func.coalesce(Quote.customer.razon_social, "").ilike(like))
            | (func.coalesce(Quote.customer.first_name, "").ilike(like))
            | (func.coalesce(Quote.customer.last_name, "").ilike(like))
        )
    total = (
        await db.execute(select(func.count()).select_from(q.order_by(None).subquery()))
    ).scalar_one()
    rows = await db.execute(
        q.order_by(Quote.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    return list(rows.scalars().all()), int(total)


async def expire_pending(db: AsyncSession, *, today: date | None = None) -> list[Quote]:
    """Marca EXPIRABLE con valid_until < hoy. Idempotente (#F06-04)."""
    today = today or datetime.now(UTC).date()
    rows = await db.execute(
        select(Quote).where(
            Quote.valid_until < today,
            Quote.status.in_(list(QuoteStatus.EXPIRABLE)),
        )
    )
    quotes = list(rows.scalars().all())
    for quote in quotes:
        quote.status = QuoteStatus.EXPIRED
    return quotes


def compute_totals(items: list[tuple[Decimal, Decimal, Decimal]]) -> tuple[Decimal, Decimal]:
    """Retorna (subtotal, total) desde tripletas (unit_price, qty, discount)."""
    subtotal = sum(((p * q) for p, q, _d in items), Decimal("0.00")).quantize(Decimal("0.01"))
    total = sum((((p * q) - d) for p, q, d in items), Decimal("0.00")).quantize(Decimal("0.01"))
    return subtotal, total


__all__ = ["get_quote", "get_by_code", "list_quotes", "next_quote_code", "expire_pending", "compute_totals", "QuoteItem"]
