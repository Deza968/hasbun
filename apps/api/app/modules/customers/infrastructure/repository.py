"""Repositorio de clientes (#F04-21)."""

from __future__ import annotations

import uuid

from app.modules.customers.domain.models import Customer
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, customer_id: uuid.UUID) -> Customer | None:
    return await db.get(Customer, customer_id)


async def get_by_dni(db: AsyncSession, dni: str) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.dni == dni))
    return result.scalars().first()


async def get_by_ruc(db: AsyncSession, ruc: str) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.ruc == ruc))
    return result.scalars().first()


async def list_customers(
    db: AsyncSession,
    *,
    search: str | None = None,
    active: bool | None = None,
    is_blocked: bool | None = None,
    type: str | None = None,  # noqa: A002
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Customer], int]:
    query = select(Customer)
    count_query = select(func.count(Customer.id))

    if search:
        like = f"%{search}%"
        condition = or_(
            Customer.first_name.ilike(like),
            Customer.last_name.ilike(like),
            Customer.razon_social.ilike(like),
            Customer.dni.ilike(like),
            Customer.ruc.ilike(like),
            Customer.phone.ilike(like),
            Customer.phone_whatsapp.ilike(like),
            Customer.email.ilike(like),
            Customer.city.ilike(like),
            Customer.district.ilike(like),
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    if active is not None:
        query = query.where(Customer.active == active)
        count_query = count_query.where(Customer.active == active)

    if is_blocked is not None:
        query = query.where(Customer.is_blocked == is_blocked)
        count_query = count_query.where(Customer.is_blocked == is_blocked)

    if type is not None:
        query = query.where(Customer.type == type.upper())
        count_query = count_query.where(Customer.type == type.upper())

    total = (await db.execute(count_query)).scalar()
    query = (
        query.order_by(Customer.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = (await db.execute(query)).scalars().all()
    return list(items), int(total or 0)
