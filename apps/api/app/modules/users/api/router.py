"""Router de usuarios (solo OWNER)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, get_current_active_user, require_permission
from app.core.exceptions import NotFoundError
from app.modules.users.application.schemas import (
    AssignRoleRequest,
    MeUpdate,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.modules.users.application.service import (
    assign_role,
    create_user,
    deactivate_user,
    remove_role,
    update_own_profile,
    update_user,
)
from app.modules.users.domain.models import User
from app.modules.users.infrastructure import repository
from fastapi import APIRouter, Depends, Query

router = APIRouter(tags=["users"])

AdminUser = Annotated[User, Depends(require_permission("usuarios.ver"))]
CreateUser = Annotated[User, Depends(require_permission("usuarios.crear"))]
EditUser = Annotated[User, Depends(require_permission("usuarios.editar"))]
DisableUser = Annotated[User, Depends(require_permission("usuarios.desactivar"))]
PermsUser = Annotated[User, Depends(require_permission("usuarios.permisos"))]


def _to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        roles=[r.code for r in user.roles],
    )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    _: AdminUser,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    is_active: bool | None = None,
) -> UserListResponse:
    """Lista usuarios (solo OWNER)."""
    items, total = await repository.list_users(
        db, offset=offset, limit=limit, is_active=is_active
    )
    return UserListResponse(items=[_to_response(u) for u in items], total=total)


@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user_endpoint(
    body: UserCreate,
    db: DbSession,
    actor: CreateUser,
) -> UserResponse:
    """Crea un usuario (solo OWNER)."""
    user = await create_user(db, data=body, created_by=actor)
    return _to_response(user)


@router.get("/users/me", response_model=UserResponse)
async def get_own_profile(
    user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Retorna el perfil del usuario autenticado."""
    return _to_response(user)


@router.put("/users/me", response_model=UserResponse)
async def update_own_profile_endpoint(
    body: MeUpdate,
    user: Annotated[User, Depends(get_current_active_user)],
    db: DbSession,
) -> UserResponse:
    """Actualiza nombre y teléfono del propio perfil (no email ni rol)."""
    user = await update_own_profile(db, user=user, data=body)
    return _to_response(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: DbSession,
    _: AdminUser,
) -> UserResponse:
    """Detalle de un usuario (solo OWNER)."""
    user = await repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Usuario no encontrado")
    return _to_response(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: DbSession,
    actor: EditUser,
) -> UserResponse:
    """Modifica un usuario (solo OWNER)."""
    user = await update_user(db, user_id=user_id, data=body, updated_by=actor)
    return _to_response(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: DbSession,
    actor: DisableUser,
) -> None:
    """Desactiva un usuario (solo OWNER, soft delete)."""
    await deactivate_user(db, user_id=user_id, deactivated_by=actor)


@router.post("/users/{user_id}/roles", response_model=UserResponse)
async def assign_role_endpoint(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    db: DbSession,
    actor: PermsUser,
) -> UserResponse:
    """Asigna un rol a un usuario (solo OWNER)."""
    user = await assign_role(db, user_id=user_id, role_code=body.role_code, assigned_by=actor)
    return _to_response(user)


@router.delete("/users/{user_id}/roles/{role_code}", response_model=UserResponse)
async def remove_role_endpoint(
    user_id: uuid.UUID,
    role_code: str,
    db: DbSession,
    actor: PermsUser,
) -> UserResponse:
    """Quita un rol a un usuario (solo OWNER)."""
    user = await remove_role(db, user_id=user_id, role_code=role_code, removed_by=actor)
    return _to_response(user)
