"""Routers de autenticación con cookies HttpOnly."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.config import settings
from app.core.dependencies import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    DbSession,
    get_current_active_user,
    get_current_user,
)
from app.core.exceptions import AuthenticationError
from app.core.redis import blocklist_access_token, revoke_session
from app.core.security import decode_token, limiter
from app.modules.auth.application.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    UserMeResponse,
)
from app.modules.auth.application.service import (
    change_password,
    get_user_permissions,
    login,
    logout,
    refresh,
)
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["auth"])

ACCESS_TTL = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400


def _set_auth_cookies(response: Response, pair) -> None:
    """Setea las cookies HttpOnly. Secure solo en producción."""
    secure = settings.is_production
    response.set_cookie(
        ACCESS_COOKIE,
        pair.access_token,
        max_age=ACCESS_TTL,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        pair.refresh_token,
        max_age=REFRESH_TTL,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/")


def _request_id(request: Request) -> uuid.UUID | None:
    raw = getattr(request.state, "request_id", None)
    if raw:
        try:
            return uuid.UUID(str(raw))
        except ValueError:
            return None
    return None


async def _build_me(db: AsyncSession, user: User) -> UserMeResponse:
    perms = await get_user_permissions(db, user)
    return UserMeResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        phone=user.phone,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        roles=[r.code for r in user.roles],
        permissions=perms,
    )


async def _load_user(db: AsyncSession, user_id: str) -> User:
    user = (
        await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    ).scalar_one_or_none()
    if user is None:
        raise AuthenticationError("Sesión inválida")
    return user


@router.post("/auth/login", response_model=UserMeResponse)
@limiter.limit("10/minute")
async def login_endpoint(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: DbSession,
) -> UserMeResponse:
    """Inicia sesión y setea cookies HttpOnly."""
    pair = await login(
        db,
        email=body.email,
        password=body.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_id=_request_id(request),
    )
    _set_auth_cookies(response, pair)
    user = await _load_user(db, decode_token(pair.access_token, "access")["sub"])
    return await _build_me(db, user)


@router.post("/auth/logout")
async def logout_endpoint(
    request: Request, response: Response, db: DbSession
) -> dict[str, str]:
    """Cierra sesión: invalida el refresh token y limpia cookies."""
    user = await get_current_user(request, db)
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if refresh_token:
        try:
            payload = decode_token(refresh_token, "refresh")
            await revoke_session(payload["sub"], payload["jti"])
        except ValueError:
            pass
    await logout(str(user.id), None, request.client.host if request.client else None)
    _clear_auth_cookies(response)
    return {"message": "Sesión cerrada"}


@router.post("/auth/refresh")
async def refresh_endpoint(request: Request, response: Response) -> dict[str, str]:
    """Rota los tokens usando la cookie de refresh."""
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise AuthenticationError("No autenticado")
    pair = await refresh(refresh_token)
    _set_auth_cookies(response, pair)
    return {"message": "Tokens renovados"}


@router.get("/auth/me", response_model=UserMeResponse)
async def me_endpoint(
    request: Request,
    user: Annotated[User, Depends(get_current_active_user)],
    db: DbSession,
) -> UserMeResponse:
    """Retorna los datos del usuario autenticado."""
    return await _build_me(db, user)


@router.post("/auth/change-password")
async def change_password_endpoint(
    request: Request,
    body: ChangePasswordRequest,
    user: Annotated[User, Depends(get_current_active_user)],
    db: DbSession,
) -> dict[str, str]:
    """Cambia la contraseña e invalida todas las sesiones activas."""
    await change_password(
        db,
        user=user,
        current_password=body.current_password,
        new_password=body.new_password,
        ip_address=request.client.host if request.client else None,
        request_id=_request_id(request),
    )
    access_token = request.cookies.get(ACCESS_COOKIE)
    if access_token:
        try:
            payload = decode_token(access_token, "access")
            await blocklist_access_token(payload["jti"], ttl=ACCESS_TTL)
        except ValueError:
            pass
    return {"message": "Contraseña actualizada"}
