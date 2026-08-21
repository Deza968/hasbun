"""Logging estructurado en JSON con request_id por request.

Nunca se loguean: passwords, tokens, claves de cifrado ni datos financieros completos.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from contextvars import ContextVar

import structlog

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def _get_request_id() -> str:
    return request_id_var.get()


def new_request_id() -> str:
    """Genera y guarda un request_id nuevo para el request actual."""
    rid = str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


def setup_logging(environment: str) -> None:
    """Configura logging JSON con structlog."""

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if environment != "production":
        shared_processors.append(structlog.dev.set_exc_info)

    shared_processors.extend(
        [
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ]
    )

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )


def get_logger(name: str = "hasbun") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    """Middleware que loguea cada request con su request_id y duración."""

    def __init__(self, app) -> None:  # noqa: ANN001
        self.app = app

    async def __call__(self, scope, receive, send) -> None:  # noqa: ANN001
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.middleware.base import _CachedRequest

        request = _CachedRequest(scope, receive)
        request_id = new_request_id()
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        status_code = 500

        async def send_wrapper(message) -> None:  # noqa: ANN001
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger = get_logger("http")
            logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            structlog.contextvars.clear_contextvars()
