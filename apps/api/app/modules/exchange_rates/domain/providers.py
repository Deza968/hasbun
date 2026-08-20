"""Interfaces de proveedores de tipo de cambio.

Separación de responsabilidades: la aplicación depende de la abstracción
`ExchangeRateProvider`; la infraestructura provee implementaciones concretas
(mock, externa). El servicio elige según settings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal


class ExchangeRateProvider(ABC):
    """Contrato de un proveedor de tipo de cambio."""

    @abstractmethod
    async def get_current_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Retorna el tipo de cambio actual. Nunca usa `float`."""
        raise NotImplementedError
