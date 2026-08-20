"""Excepciones del módulo de atributos."""

from __future__ import annotations

from app.core.exceptions import ConflictError


class DuplicateAttributeValueError(ConflictError):
    """Ya existe un valor con ese texto para el atributo."""
