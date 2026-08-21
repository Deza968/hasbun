"""Repository de usuarios."""

from __future__ import annotations

import uuid

from app.modules.users.domain.models import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    return (
        await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    ).scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    return (
        await db.execute(select(User).where(func.lower(User.username) == username.lower()))
    ).scalar_one_or_none()


async def list_users(
    db: AsyncSession, *, offset: int = 0, limit: int = 50, is_active: bool | None = None
) -> tuple[list[User], int]:
    query = select(User)
    count_query = select(func.count(User.id))
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    total = (await db.execute(count_query)).scalar_one()
    rows = (
        await db.execute(query.order_by(User.created_at.desc()).offset(offset).limit(limit))
    ).scalars().all()
    return list(rows), total


async def create(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update(db: AsyncSession, user: User) -> User:
    await db.commit()
    await db.refresh(user)
    return user
