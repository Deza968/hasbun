"""CORS, headers de seguridad HTTP, TrustedHost, rate limiting y JWT.

- CORS estricto con orígenes permitidos desde settings.
- Headers de seguridad: X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
- TrustedHostMiddleware en producción.
- Rate limiting con slowapi + Redis (100 req/min por IP; auth: 10/min).
- JWT (access + refresh) firmados con HS256.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["100/minute"],
)

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


def hash_password(password: str) -> str:
    """Genera el hash bcrypt de una contraseña."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:  # noqa: S105, S106
    """Crea un JWT firmado con expiración y jti único."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str) -> str:
    """Crea un access token (TTL configurable en minutos)."""
    return _create_token(
        subject, "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(subject: str) -> str:
    """Crea un refresh token (TTL configurable en días)."""
    return _create_token(
        subject, "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decodifica y valida un JWT. Retorna el payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("token inválido o expirado") from exc
    if payload.get("type") != expected_type:
        raise ValueError("tipo de token incorrecto")
    if not payload.get("sub"):
        raise ValueError("token sin subject")
    return payload


class SecurityHeadersMiddleware:
    """Agrega headers de seguridad HTTP a todas las respuestas."""

    def __init__(self, app) -> None:  # noqa: ANN001
        self.app = app

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message) -> None:  # noqa: ANN001
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                for key, value in SECURITY_HEADERS.items():
                    headers.append((key.lower().encode(), value.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def setup_security(app: FastAPI) -> None:
    """Aplica todos los middlewares de seguridad y rate limiting."""
    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded, _rate_limit_exceeded_handler  # type: ignore[arg-type]
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.is_production:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["hasbun.pe", "www.hasbun.pe", "api.hasbun.pe"],
        )

    app.add_middleware(SecurityHeadersMiddleware)
