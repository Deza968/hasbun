"""Router de permisos y overrides por usuario (solo OWNER)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.core.redis import invalidate_permission_cache
from app.modules.audit.application.service import log
from app.modules.permissions.domain.models import (
    Permission,
    UserPermissionOverride,
)
from app.modules.users.application.schemas import AssignPermissionRequest
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

router = APIRouter(tags=["permissions"])

ViewPerms = Annotated[User, Depends(require_permission("roles.ver"))]
EditPerms = Annotated[User, Depends(require_permission("usuarios.permisos"))]


class PermissionResponse(BaseModel):
    id: uuid.UUID
    codename: str
    description: str | None
    module: str


@router.get("/permissions", response_model=list[PermissionResponse])
async def list_permissions(
    db: DbSession,
    _: ViewPerms,
) -> list[PermissionResponse]:
    """Lista todos los permisos (solo OWNER)."""
    perms = (
        await db.execute(
            select(Permission).order_by(Permission.module, Permission.codename)
        )
    ).scalars().all()
    return [
        PermissionResponse(id=p.id, codename=p.codename, description=p.description, module=p.module)
        for p in perms
    ]


@router.post("/users/{user_id}/permissions", status_code=204)
async def set_permission_override(
    user_id: uuid.UUID,
    body: AssignPermissionRequest,
    db: DbSession,
    actor: EditPerms,
) -> None:
    """Crea o actualiza un override de permiso individual (solo OWNER)."""
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    perm = (
        await db.execute(select(Permission).where(Permission.codename == body.codename))
    ).scalar_one_or_none()
    if perm is None:
        raise NotFoundError(f"Permiso no encontrado: {body.codename}")

    existing = (
        await db.execute(
            select(UserPermissionOverride).where(
                UserPermissionOverride.user_id == user.id,
                UserPermissionOverride.permission_id == perm.id,
            )
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.granted = body.granted
        existing.reason = body.reason
        existing.assigned_by = actor.id
    else:
        db.add(
            UserPermissionOverride(
                user_id=user.id,
                permission_id=perm.id,
                granted=body.granted,
                reason=body.reason,
                assigned_by=actor.id,
            )
        )
    await db.commit()
    await invalidate_permission_cache(str(user.id))
    await log(
        action="SET_PERMISSION_OVERRIDE",
        module="permissions",
        user_id=actor.id,
        entity_type="User",
        entity_id=user.id,
        new_values={"codename": body.codename, "granted": body.granted, "reason": body.reason},
    )


@router.delete("/users/{user_id}/permissions/{permission_id}", status_code=204)
async def delete_permission_override(
    user_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: DbSession,
    actor: EditPerms,
) -> None:
    """Elimina un override de permiso individual (solo OWNER)."""
    override = (
        await db.execute(
            select(UserPermissionOverride).where(
                UserPermissionOverride.user_id == user_id,
                UserPermissionOverride.permission_id == permission_id,
            )
        )
    ).scalar_one_or_none()
    if override is None:
        raise NotFoundError("Override no encontrado")
    await db.delete(override)
    await db.commit()
    await invalidate_permission_cache(str(user_id))
    await log(
        action="DELETE_PERMISSION_OVERRIDE",
        module="permissions",
        user_id=actor.id,
        entity_type="User",
        entity_id=user_id,
        old_values={"permission_id": str(permission_id)},
    )
