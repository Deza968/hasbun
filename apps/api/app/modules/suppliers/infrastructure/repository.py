"""Repositorio de proveedores (#F03-07)."""

from __future__ import annotations

import uuid

from app.modules.suppliers.domain.models import Supplier
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, supplier_id: uuid.UUID) -> Supplier | None:
    return await db.get(Supplier, supplier_id)


async def get_by_ruc(db: AsyncSession, ruc: str) -> Supplier | None:
    result = await db.execute(select(Supplier).where(Supplier.ruc == ruc))
    return result.scalars().first()


async def list_suppliers(
    db: AsyncSession,
    *,
    search: str | None = None,
    active: bool | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Supplier], int]:
    query = select(Supplier)
    count_query = select(func.count(Supplier.id))

    if search:
        like = f"%{search}%"
        condition = or_(
            Supplier.razon_social.ilike(like),
            Supplier.nombre_comercial.ilike(like),
            Supplier.ruc.ilike(like),
            Supplier.contacto_nombre.ilike(like),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)
    if active is not None:
        query = query.where(Supplier.active == active)
        count_query = count_query.where(Supplier.active == active)

    total = (await db.execute(count_query)).scalar()
    query = (
        query.order_by(Supplier.razon_social.asc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = (await db.execute(query)).scalars().unique().all()
    return list(items), int(total or 0)
