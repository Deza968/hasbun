"""Router de roles y asignación de permisos a roles (solo OWNER)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.core.exceptions import NotFoundError
from app.modules.audit.application.service import log
from app.modules.permissions.domain.models import Permission
from app.modules.roles.domain.models import Role
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

router = APIRouter(tags=["roles"])

ViewRoles = Annotated[User, Depends(require_permission("roles.ver"))]
EditRoles = Annotated[User, Depends(require_permission("roles.editar"))]


class AssignPermissionBody(BaseModel):
    codename: str


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None
    is_system: bool
    permissions: list[str]


class PermissionResponse(BaseModel):
    id: uuid.UUID
    codename: str
    description: str | None
    module: str


def _role_to_response(role: Role) -> RoleResponse:
    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        is_system=role.is_system,
        permissions=sorted(p.codename for p in role.permissions),
    )


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    db: DbSession,
    _: ViewRoles,
) -> list[RoleResponse]:
    """Lista todos los roles (solo OWNER)."""
    roles = (await db.execute(select(Role))).scalars().all()
    return [_role_to_response(r) for r in roles]


@router.get("/roles/{role_id}/permissions", response_model=list[PermissionResponse])
async def role_permissions(
    role_id: uuid.UUID,
    db: DbSession,
    _: ViewRoles,
) -> list[PermissionResponse]:
    """Permisos de un rol (solo OWNER)."""
    role = await db.get(Role, role_id)
    if role is None:
        raise NotFoundError("Rol no encontrado")
    return [
        PermissionResponse(id=p.id, codename=p.codename, description=p.description, module=p.module)
        for p in role.permissions
    ]


@router.post("/roles/{role_id}/permissions", response_model=RoleResponse)
async def assign_permission_to_role(
    role_id: uuid.UUID,
    body: AssignPermissionBody,
    db: DbSession,
    actor: EditRoles,
) -> RoleResponse:
    """Asigna un permiso a un rol (solo OWNER)."""
    role = await db.get(Role, role_id)
    if role is None:
        raise NotFoundError("Rol no encontrado")
    perm = (
        await db.execute(select(Permission).where(Permission.codename == body.codename))
    ).scalar_one_or_none()
    if perm is None:
        raise NotFoundError(f"Permiso no encontrado: {body.codename}")
    if perm not in role.permissions:
        role.permissions.append(perm)
        await db.commit()
        await log(
            action="ASSIGN_PERMISSION_TO_ROLE",
            module="roles",
            user_id=actor.id,
            entity_type="Role",
            entity_id=role.id,
            new_values={"codename": body.codename},
        )
    return _role_to_response(role)


@router.delete("/roles/{role_id}/permissions/{permission_id}", response_model=RoleResponse)
async def remove_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: DbSession,
    actor: EditRoles,
) -> RoleResponse:
    """Quita un permiso de un rol (solo OWNER)."""
    role = await db.get(Role, role_id)
    if role is None:
        raise NotFoundError("Rol no encontrado")
    role.permissions = [p for p in role.permissions if p.id != permission_id]
    await db.commit()
    await log(
        action="REMOVE_PERMISSION_FROM_ROLE",
        module="roles",
        user_id=actor.id,
        entity_type="Role",
        entity_id=role.id,
        old_values={"permission_id": str(permission_id)},
    )
    return _role_to_response(role)
