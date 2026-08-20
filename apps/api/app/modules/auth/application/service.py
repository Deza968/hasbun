"""Servicio de autenticación: login, logout, refresh y sesiones Redis."""

from __future__ import annotations

import uuid

from app.core.exceptions import (
    AuthenticationError,
    BusinessRuleError,
    ValidationError,
)
from app.core.redis import (
    refresh_session_exists,
    register_login_failure,
    reset_login_failures,
    revoke_all_sessions,
    revoke_session,
    store_refresh_session,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.modules.audit.application.service import log
from app.modules.auth.application.schemas import TokenPair
from app.modules.permissions.domain.models import (
    Permission,
    UserPermissionOverride,
)
from app.modules.roles.domain.models import Role
from app.modules.users.domain.models import User
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def login(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    ip_address: str | None,
    user_agent: str | None,
    request_id: uuid.UUID | None = None,
) -> TokenPair:
    """Autentica un usuario y genera el par de tokens."""
    user = (
        await db.execute(select(User).where(func.lower(User.email) == email.lower()))
    ).scalar_one_or_none()

    valid = user is not None and verify_password(password, user.password_hash)
    if not valid or user is None or not user.is_active:
        await log(
            action="LOGIN_FAILED",
            module="auth",
            user_id=user.id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )
        if ip_address and await register_login_failure(ip_address):
            raise BusinessRuleError(
                "Demasiados intentos fallidos. Intente en 15 minutos.",
                {"code": "LOGIN_BLOCKED"},
            )
        # Error genérico: no revelar si el email existe
        raise AuthenticationError("Credenciales inválidas")

    if ip_address:
        await reset_login_failures(ip_address)
    user.last_login_at = func.now()
    await db.commit()

    pair = await _issue_tokens(str(user.id))
    await log(
        action="LOGIN_SUCCESS",
        module="auth",
        user_id=user.id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )
    return pair


async def refresh(refresh_token: str) -> TokenPair:
    """Rota el refresh token generando un par nuevo."""
    try:
        payload = decode_token(refresh_token, "refresh")
    except ValueError as exc:
        raise AuthenticationError("Sesión inválida o expirada") from exc

    user_id = payload["sub"]
    jti = payload["jti"]
    if not await refresh_session_exists(user_id, jti):
        raise AuthenticationError("Sesión inválida o expirada")

    await revoke_session(user_id, jti)
    return await _issue_tokens(user_id)


async def logout(user_id: str, refresh_jti: str | None, ip_address: str | None) -> None:
    """Invalida la sesión de refresh del usuario."""
    if refresh_jti:
        await revoke_session(user_id, refresh_jti)
    await log(
        action="LOGOUT",
        module="auth",
        user_id=uuid.UUID(user_id),
        ip_address=ip_address,
    )


async def _issue_tokens(user_id: str) -> TokenPair:
    access = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    refresh_payload = decode_token(refresh_token, "refresh")
    await store_refresh_session(user_id, refresh_payload["jti"])
    return TokenPair(
        access_token=access,
        refresh_token=refresh_token,
        token_type="bearer",  # noqa: S106
    )


async def get_user_permissions(db: AsyncSession, user: User) -> list[str]:
    """Calcula los permisos efectivos de un usuario (RBAC + overrides).

    Orden de resolución:
    1. Override granted=False → denegar
    2. Override granted=True → permitir
    3. RolePermission del rol → verificar
    4. is_superuser → todo
    """
    if user.is_superuser:
        return ["*"]

    role_ids = [r.id for r in user.roles]
    result: set[str] = set()
    if role_ids:
        rows = (
            await db.execute(
                select(Permission.codename)
                .join(Permission.roles)
                .where(Role.id.in_(role_ids))
            )
        ).scalars().all()
        result.update(rows)

    overrides = (
        await db.execute(
            select(UserPermissionOverride, Permission.codename)
            .join(Permission, Permission.id == UserPermissionOverride.permission_id)
            .where(UserPermissionOverride.user_id == user.id)
        )
    ).all()
    for override, codename in overrides:
        if override.granted:
            result.add(codename)
        else:
            result.discard(codename)

    return sorted(result)


async def change_password(
    db: AsyncSession,
    *,
    user: User,
    current_password: str,
    new_password: str,
    ip_address: str | None = None,
    request_id: uuid.UUID | None = None,
) -> None:
    """Cambia la contraseña del usuario e invalida todas sus sesiones."""
    if not verify_password(current_password, user.password_hash):
        raise ValidationError("La contraseña actual es incorrecta")

    user.password_hash = hash_password(new_password)
    await db.commit()
    await revoke_all_sessions(str(user.id))
    await log(
        action="CHANGE_PASSWORD",
        module="auth",
        user_id=user.id,
        ip_address=ip_address,
        request_id=request_id,
    )
