"""Repo Sales."""

from __future__ import annotations

import uuid

from app.modules.sales.domain.models import Sale
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, sale_id: uuid.UUID):
    return await db.get(Sale, sale_id)


async def get_by_code(db: AsyncSession, code: str):
    return (await db.execute(select(Sale).where(Sale.code == code))).scalar_one_or_none()


async def get_by_idempotency(db: AsyncSession, key: str):
    return (await db.execute(select(Sale).where(Sale.idempotency_key == key))).scalar_one_or_none()


async def list_sales(db: AsyncSession, *, page=1, per_page=20, status=None, sale_type=None):
    q = select(Sale)
    cq = select(func.count(Sale.id))
    if status:
        q = q.where(Sale.status == status)
        cq = cq.where(Sale.status == status)
    if sale_type:
        q = q.where(Sale.sale_type == sale_type)
        cq = cq.where(Sale.sale_type == sale_type)
    total = (await db.execute(cq)).scalar()
    items = (await db.execute(q.order_by(Sale.created_at.desc()).offset((page-1)*per_page).limit(per_page))).scalars().unique().all()
    return list(items), int(total or 0)
