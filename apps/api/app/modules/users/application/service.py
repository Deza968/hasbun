"""Servicios de gestión de usuarios (solo OWNER)."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.redis import invalidate_permission_cache
from app.core.security import hash_password
from app.modules.audit.application.service import log
from app.modules.roles.domain.models import Role
from app.modules.users.domain.models import User
from app.modules.users.infrastructure import repository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(
    db: AsyncSession,
    *,
    data,
    created_by: User,
) -> User:
    if await repository.get_by_email(db, data.email):
        raise ConflictError("Ya existe un usuario con ese email")
    if await repository.get_by_username(db, data.username):
        raise ConflictError("Ya existe un usuario con ese username")

    user = User(
        email=data.email,
        username=data.username,
        full_name=data.full_name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        is_active=True,
        is_superuser=False,
    )
    for code in data.role_codes:
        role = (
            await db.execute(select(Role).where(Role.code == code))
        ).scalar_one_or_none()
        if role is None:
            raise NotFoundError(f"Rol no encontrado: {code}")
        user.roles.append(role)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    await log(
        action="CREATE_USER",
        module="users",
        user_id=created_by.id,
        entity_type="User",
        entity_id=user.id,
        new_values={"email": user.email, "username": user.username},
    )
    return user


async def update_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    data,
    updated_by: User,
) -> User:
    user = await repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")

    old = {"full_name": user.full_name, "phone": user.phone, "is_active": user.is_active}
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.is_active is not None:
        user.is_active = data.is_active
    await db.commit()
    await db.refresh(user)
    await log(
        action="UPDATE_USER",
        module="users",
        user_id=updated_by.id,
        entity_type="User",
        entity_id=user.id,
        old_values=old,
        new_values={
            "full_name": user.full_name,
            "phone": user.phone,
            "is_active": user.is_active,
        },
    )
    return user


async def deactivate_user(
    db: AsyncSession, *, user_id: uuid.UUID, deactivated_by: User
) -> User:
    user = await repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    await log(
        action="DEACTIVATE_USER",
        module="users",
        user_id=deactivated_by.id,
        entity_type="User",
        entity_id=user.id,
        new_values={"is_active": False},
    )
    return user


async def assign_role(
    db: AsyncSession, *, user_id: uuid.UUID, role_code: str, assigned_by: User
) -> User:
    user = await repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    role = (
        await db.execute(select(Role).where(Role.code == role_code))
    ).scalar_one_or_none()
    if role is None:
        raise NotFoundError(f"Rol no encontrado: {role_code}")
    if role not in user.roles:
        user.roles.append(role)
        await db.commit()
    await invalidate_permission_cache(str(user.id))
    await log(
        action="ASSIGN_ROLE",
        module="users",
        user_id=assigned_by.id,
        entity_type="User",
        entity_id=user.id,
        new_values={"role": role_code},
    )
    return user


async def remove_role(
    db: AsyncSession, *, user_id: uuid.UUID, role_code: str, removed_by: User
) -> User:
    user = await repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    user.roles = [r for r in user.roles if r.code != role_code]
    await db.commit()
    await invalidate_permission_cache(str(user.id))
    await log(
        action="REMOVE_ROLE",
        module="users",
        user_id=removed_by.id,
        entity_type="User",
        entity_id=user.id,
        old_values={"role": role_code},
    )
    return user
