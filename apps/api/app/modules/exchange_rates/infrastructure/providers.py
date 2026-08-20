"""Provider de tipo de cambio (interfaz + implementaciones)."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from decimal import Decimal

from app.core.config import settings

logger = logging.getLogger("hasbun.exchange_rates")


class ExchangeRateProvider(ABC):
    """Interfaz para obtener el tipo de cambio desde una fuente externa."""

    @abstractmethod
    async def get_current_rate(
        self, currency_from: str, currency_to: str
    ) -> Decimal:
        """Retorna la tasa de cambio vigente para el par."""


class MockExchangeRateProvider(ExchangeRateProvider):
    """Devuelve una tasa fija configurable. No hace llamadas externas."""

    def __init__(self) -> None:
        self._rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN))

    async def get_current_rate(
        self, currency_from: str, currency_to: str
    ) -> Decimal:
        if currency_from == currency_to:
            return Decimal("1.0000")
        if currency_from == "USD" and currency_to == "PEN":
            return self._rate
        if currency_from == "PEN" and currency_to == "USD":
            return (Decimal("1") / self._rate).quantize(Decimal("0.0001"))
        logger.warning(
            "Par de monedas no soportado por el provider mock: %s → %s",
            currency_from,
            currency_to,
        )
        return Decimal("0.0000")


class ExternalExchangeRateProvider(ExchangeRateProvider):
    """Stub para integración futura (SUNAT/BCP).

    No implementado en FASE 02. Cuando se implemente, debe cumplir la
    interfaz `ExchangeRateProvider` y usar Decimal para evitar pérdida de
    precisión.
    """

    async def get_current_rate(
        self, currency_from: str, currency_to: str
    ) -> Decimal:
        raise NotImplementedError(
            "ExternalExchangeRateProvider no está implementado en FASE 02"
        )


def get_provider() -> ExchangeRateProvider:
    """Factory que selecciona el provider según settings."""
    if settings.EXCHANGE_RATE_PROVIDER == "mock":
        return MockExchangeRateProvider()
    return ExternalExchangeRateProvider()
