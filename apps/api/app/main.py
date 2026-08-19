"""Aplicación principal FastAPI de Hasbun API.

Inicializa configuración, logging, seguridad, excepciones y routers.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, setup_logging
from app.core.security import setup_security
from app.modules.health.api.router import router as health_router

setup_logging(settings.ENVIRONMENT)

app = FastAPI(
    title="Hasbun API",
    description="Backend ERP + POS + Servicios de Inversiones Hasbun",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

register_exception_handlers(app)
setup_security(app)

app.add_middleware(RequestLoggingMiddleware)

app.include_router(health_router, prefix="/api/v1")
