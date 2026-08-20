"""Aplicación principal FastAPI de Hasbun API.

Inicializa configuración, logging, seguridad, excepciones y routers.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import RequestLoggingMiddleware, setup_logging
from app.core.security import setup_security
from app.modules.audit.api.router import router as audit_router
from app.modules.auth.api.router import router as auth_router
from app.modules.brands.api.router import router as brands_router
from app.modules.categories.api.router import router as categories_router
from app.modules.exchange_rates.api.router import router as exchange_rates_router
from app.modules.files.api.router import router as files_router
from app.modules.health.api.router import router as health_router
from app.modules.permissions.api.router import router as permissions_router
from app.modules.products.api.attributes_router import router as attributes_router
from app.modules.products.api.router import router as products_router
from app.modules.roles.api.router import router as roles_router
from app.modules.users.api.router import router as users_router

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
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(roles_router, prefix="/api/v1")
app.include_router(permissions_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(exchange_rates_router, prefix="/api/v1")
app.include_router(brands_router, prefix="/api/v1")
app.include_router(categories_router, prefix="/api/v1")
app.include_router(attributes_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")
app.include_router(files_router, prefix="/api/v1")
