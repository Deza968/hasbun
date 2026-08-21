"""Excepciones del módulo de categorías."""

from __future__ import annotations

from app.core.exceptions import ConflictError


class CategoryHasProductsError(ConflictError):
    """La categoría tiene productos activos y no puede eliminarse."""


class CategoryHasChildrenError(ConflictError):
    """La categoría tiene subcategorías y no puede eliminarse."""
