"""Repositorio de productos (#F02-09)."""

from __future__ import annotations

import uuid

from app.modules.products.domain.models import Product
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    return await db.get(Product, product_id)


async def get_by_sku(db: AsyncSession, sku: str) -> Product | None:
    result = await db.execute(select(Product).where(Product.sku == sku))
    return result.scalars().first()


async def get_by_barcode(db: AsyncSession, barcode: str) -> Product | None:
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    return result.scalars().first()


async def get_by_slug(db: AsyncSession, slug: str) -> Product | None:
    result = await db.execute(select(Product).where(Product.slug == slug))
    return result.scalars().first()


async def list_products(
    db: AsyncSession,
    *,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    brand_id: uuid.UUID | None = None,
    active: bool | None = None,
    published: bool | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Product], int]:
    query = select(Product)
    count_query = select(func.count(Product.id))

    if search:
        like = f"%{search}%"
        condition = or_(
            Product.name.ilike(like),
            Product.sku.ilike(like),
            Product.barcode.ilike(like),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)
    if category_id:
        query = query.where(Product.category_id == category_id)
        count_query = count_query.where(Product.category_id == category_id)
    if brand_id:
        query = query.where(Product.brand_id == brand_id)
        count_query = count_query.where(Product.brand_id == brand_id)
    if active is not None:
        query = query.where(Product.active == active)
        count_query = count_query.where(Product.active == active)
    if published is not None:
        query = query.where(Product.published == published)
        count_query = count_query.where(Product.published == published)

    total = (await db.execute(count_query)).scalar()
    query = query.order_by(Product.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    items = (await db.execute(query)).scalars().unique().all()
    return list(items), int(total or 0)
