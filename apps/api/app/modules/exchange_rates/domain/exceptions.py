"""Excepciones del módulo de tipo de cambio."""

from __future__ import annotations

from app.core.exceptions import NotFoundError


class ExchangeRateNotFoundError(NotFoundError):
    """No existe un tipo de cambio vigente para el par solicitado."""
