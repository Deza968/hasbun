"""Dependencies de FastAPI para autenticación y permisos."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.redis import get_permission_cache, is_access_token_blocked, set_permission_cache
from app.core.security import decode_token
from app.database.session import get_db
from app.modules.auth.application.service import get_user_permissions
from app.modules.users.domain.models import User

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, db: DbSession) -> User:
    """Lee la cookie de access token, valida y retorna el usuario."""
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise AuthenticationError("No autenticado")

    try:
        payload = decode_token(token, "access")
    except ValueError as exc:
        raise AuthenticationError("Sesión inválida o expirada") from exc

    if await is_access_token_blocked(payload["jti"]):
        raise AuthenticationError("Sesión inválida o expirada")

    user = (
        await db.execute(select(User).where(User.id == payload["sub"]))
    ).scalar_one_or_none()
    if user is None:
        raise AuthenticationError("Sesión inválida o expirada")
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verifica que el usuario esté activo."""
    if not user.is_active:
        raise AuthenticationError("Usuario inactivo")
    return user


def require_permission(codename: str) -> Callable:
    """Factory que retorna una dependency que verifica un permiso.

    Orden: overrides → RolePermission → superuser. Con caché en Redis (5 min).
    """

    async def dependency(
        user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if user.is_superuser:
            return user

        perms = await get_permission_cache(str(user.id))
        if perms is None:
            from app.database.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                perms = await get_user_permissions(session, user)
            await set_permission_cache(str(user.id), perms)

        if codename in perms or "*" in perms:
            return user
        raise AuthorizationError(f"Permiso requerido: {codename}")

    return dependency
