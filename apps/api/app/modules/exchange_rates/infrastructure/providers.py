"""Implementaciones de proveedores de tipo de cambio.

- `MockExchangeRateProvider`: tasa fija configurable. No hace llamadas externas.
- `ExternalExchangeRateProvider`: stub documentado para SUNAT/BCP (futuro).
  No implementado: registra un log y lanza si se llama.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from app.core.config import settings
from app.modules.exchange_rates.domain.providers import ExchangeRateProvider

logger = logging.getLogger("hasbun.exchange_rates")


class MockExchangeRateProvider(ExchangeRateProvider):
    """Devuelve la tasa fija de settings (por defecto USD→PEN = 3.75)."""

    async def get_current_rate(self, from_currency: str, to_currency: str) -> Decimal:
        if from_currency.upper() == to_currency.upper():
            return Decimal("1.0000")
        if from_currency.upper() == "USD" and to_currency.upper() == "PEN":
            return Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN)).quantize(Decimal("0.0001"))
        if from_currency.upper() == "PEN" and to_currency.upper() == "USD":
            rate = Decimal(str(settings.MOCK_EXCHANGE_RATE_USD_PEN)).quantize(Decimal("0.0001"))
            return (Decimal("1.0000") / rate).quantize(Decimal("0.0001"))
        # Inversa desconocida: invertir la tasa directa del par conocido
        logger.warning(
            "Par de monedas no soportado por mock: %s→%s", from_currency, to_currency
        )
        return Decimal("1.0000")


class ExternalExchangeRateProvider(ExchangeRateProvider):
    """Stub para integración futura con SUNAT/BCP.

    No está implementado a propósito (#F02-01 tarea: "preparar stub vacío
    documentado, no implementar"). Lanza NotImplementedError si se instancia.
    """

    async def get_current_rate(self, from_currency: str, to_currency: str) -> Decimal:
        raise NotImplementedError(
            "ExternalExchangeRateProvider no implementado: pendiente SUNAT/BCP"
        )


def build_provider() -> ExchangeRateProvider:
    """Factory según `settings.EXCHANGE_RATE_PROVIDER`."""
    provider = settings.EXCHANGE_RATE_PROVIDER.lower()
    if provider == "mock":
        return MockExchangeRateProvider()
    return ExternalExchangeRateProvider()
