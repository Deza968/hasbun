"""Excepciones del módulo de productos."""

from __future__ import annotations

from app.core.exceptions import BusinessRuleError, ConflictError


class ProductHasActiveReferencesError(ConflictError):
    """El producto tiene ventas/movimientos activos y no puede eliminarse."""


class DuplicateSerialNumberError(ConflictError):
    """Ya existe una unidad cargada con ese número de serie/IMEI."""


class InvalidPriceRuleError(BusinessRuleError):
    """La regla de precio no es válida."""
