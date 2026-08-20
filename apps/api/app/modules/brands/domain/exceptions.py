"""Excepciones del módulo de marcas."""

from __future__ import annotations

from app.core.exceptions import ConflictError


class BrandHasProductsError(ConflictError):
    """La marca tiene productos asociados y no puede eliminarse."""
