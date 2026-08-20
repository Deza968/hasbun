"""Repository de marcas."""

from __future__ import annotations

import uuid

from app.modules.brands.domain.models import Brand
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, brand_id: uuid.UUID) -> Brand | None:
    return await db.get(Brand, brand_id)


async def get_by_slug(db: AsyncSession, slug: str) -> Brand | None:
    return (
        await db.execute(select(Brand).where(Brand.slug == slug))
    ).scalar_one_or_none()


async def list_brands(
    db: AsyncSession, *, active: bool | None = None
) -> list[Brand]:
    query = select(Brand)
    if active is not None:
        query = query.where(Brand.active == active)
    return list((await db.execute(query.order_by(Brand.name))).scalars().all())


async def count_products(db: AsyncSession, brand_id: uuid.UUID) -> int:
    from app.modules.products.domain.models import Product

    return (
        await db.execute(
            select(func.count(Product.id)).where(Product.brand_id == brand_id)
        )
    ).scalar_one()


async def create(db: AsyncSession, brand: Brand) -> Brand:
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


async def update(db: AsyncSession, brand: Brand) -> Brand:
    await db.commit()
    await db.refresh(brand)
    return brand
