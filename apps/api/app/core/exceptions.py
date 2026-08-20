"""Excepciones de dominio y handlers globales con formato estándar.

Formato de respuesta de error:
{
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "...",
    "details": {},
    "request_id": "..."
  }
}
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class HasbunException(Exception):
    """Excepción base del dominio."""

    status_code = 500
    code = "HASBUN_ERROR"

    def __init__(self, message: str = "", details: dict[str, Any] | None = None) -> None:
        self.message = message or self.__doc__ or self.code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(HasbunException):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(HasbunException):
    status_code = 422
    code = "VALIDATION_ERROR"


class AuthenticationError(HasbunException):
    status_code = 401
    code = "AUTHENTICATION_ERROR"


class AuthorizationError(HasbunException):
    status_code = 403
    code = "AUTHORIZATION_ERROR"


class BusinessRuleError(HasbunException):
    status_code = 400
    code = "BUSINESS_RULE_VIOLATION"


class ConflictError(HasbunException):
    status_code = 409
    code = "CONFLICT"


class InsufficientStockError(BusinessRuleError):
    code = "INSUFFICIENT_STOCK"


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "")


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": _get_request_id(request),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los handlers de error en la aplicación."""

    @app.exception_handler(HasbunException)
    async def hasbun_exception_handler(
        request: Request, exc: HasbunException
    ) -> JSONResponse:
        return _error_response(
            request, exc.status_code, exc.code, exc.message, exc.details
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for err in exc.errors():
            clean = {k: v for k, v in err.items() if k != "ctx"}
            errors.append(clean)
        return _error_response(
            request, 422, "VALIDATION_ERROR", "Datos de entrada inválidos", {"errors": errors}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _error_response(request, exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        if not __import__("app.core.config", fromlist=["settings"]).settings.is_production:
            import logging

            logging.getLogger("hasbun.error").exception(
                "Unhandled error", exc_info=exc
            )
        return _error_response(
            request, 500, "INTERNAL_ERROR", "Error interno del servidor"
        )
