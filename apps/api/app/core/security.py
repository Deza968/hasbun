"""CORS, headers de seguridad HTTP, TrustedHost y rate limiting.

- CORS estricto con orígenes permitidos desde settings.
- Headers de seguridad: X-Frame-Options, X-Content-Type-Options, Referrer-Policy.
- TrustedHostMiddleware en producción.
- Rate limiting con slowapi + Redis (100 req/min por IP; auth: 10/min).
"""

from __future__ import annotations

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
