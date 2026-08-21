"""Repositorio de compras (#F03-09)."""

from __future__ import annotations

import uuid

from app.modules.purchases.domain.models import Purchase, PurchaseItem
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def get_by_id(db: AsyncSession, purchase_id: uuid.UUID) -> Purchase | None:
    result = await db.execute(
        select(Purchase)
        .where(Purchase.id == purchase_id)
        .options(selectinload(Purchase.items).selectinload(PurchaseItem.product))
    )
    return result.scalars().first()


async def get_by_code(db: AsyncSession, code: str) -> Purchase | None:
    result = await db.execute(select(Purchase).where(Purchase.code == code))
    return result.scalars().first()


async def list_purchases(
    db: AsyncSession,
    *,
    supplier_id: uuid.UUID | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Purchase], int]:
    query = select(Purchase)
    count_query = select(func.count(Purchase.id))

    if supplier_id:
        query = query.where(Purchase.supplier_id == supplier_id)
        count_query = count_query.where(Purchase.supplier_id == supplier_id)
    if status:
        query = query.where(Purchase.status == status)
        count_query = count_query.where(Purchase.status == status)

    total = (await db.execute(count_query)).scalar()
    query = (
        query.order_by(Purchase.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = (await db.execute(query)).scalars().unique().all()
    return list(items), int(total or 0)
