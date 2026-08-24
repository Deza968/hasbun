"""Interfaz de proveedor de WhatsApp y implementaciones (#F06-07/#F06-08).

La aplicación NUNCA depende de un proveedor externo concreto: se programa
contra `WhatsAppProvider`. La selección se hace con settings.WHATSAPP_PROVIDER:
- "mock"   → MockWhatsAppProvider (desarrollo/testing, sin HTTP real)
- "twilio" → TwilioWhatsAppProvider (stub, no implementado)
- "meta"   → MetaWhatsAppProvider (stub, no implementado)

Ver docs/whatsapp.md para cómo agregar un proveedor nuevo.
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger("hasbun.whatsapp.provider")


@dataclass
class WhatsAppSendResult:
    """Resultado normalizado de un envío."""

    ok: bool
    provider_message_id: str | None = None
    error: str | None = None
    raw_response: dict = field(default_factory=dict)


class WhatsAppProvider(ABC):
    """Contrato que debe cumplir cualquier proveedor de WhatsApp."""

    @abstractmethod
    async def send_message(
        self,
        recipient: str,
        template_name: str,
        variables: dict,
        rendered_body: str,
    ) -> WhatsAppSendResult:
        """Envía un mensaje. Nunca lanza excepciones de negocio: devuelve resultado."""
        ...


class MockWhatsAppProvider(WhatsAppProvider):
    """Proveedor mock: loguea a stdout y simula fallos configurables.

    - No hace llamadas HTTP reales.
    - Si WHATSAPP_MOCK_FAIL_RATE > 0 falla aleatoriamente con esa probabilidad
      (útil para probar el retry/backoff en desarrollo).
    """

    def __init__(self, fail_rate: float | None = None) -> None:
        self.fail_rate = (
            float(fail_rate) if fail_rate is not None else float(settings.WHATSAPP_MOCK_FAIL_RATE)
        )

    async def send_message(
        self,
        recipient: str,
        template_name: str,
        variables: dict,
        rendered_body: str,
    ) -> WhatsAppSendResult:
        if self.fail_rate > 0 and random.random() < self.fail_rate:  # noqa: S311 — simulación, no crypto
            return WhatsAppSendResult(ok=False, error="mock simulated failure")
        print(
            f"[WHATSAPP MOCK] to={recipient} template={template_name}\n"
            f"  body={rendered_body}",
            flush=True,
        )
        logger.info("Mock WhatsApp enviado a %s (template=%s)", recipient, template_name)
        return WhatsAppSendResult(
            ok=True,
            provider_message_id=f"mock-{random.randint(10**8, 10**9 - 1)}",  # noqa: S311
            raw_response={"provider": "mock", "recipient": recipient},
        )


class TwilioWhatsAppProvider(WhatsAppProvider):
    """Stub de Twilio — NO implementado (producción futura)."""

    async def send_message(
        self,
        recipient: str,
        template_name: str,
        variables: dict,
        rendered_body: str,
    ) -> WhatsAppSendResult:
        raise NotImplementedError("TwilioWhatsAppProvider no implementado aún")


class MetaWhatsAppProvider(WhatsAppProvider):
    """Stub de Meta Cloud API — NO implementado (producción futura)."""

    async def send_message(
        self,
        recipient: str,
        template_name: str,
        variables: dict,
        rendered_body: str,
    ) -> WhatsAppSendResult:
        raise NotImplementedError("MetaWhatsAppProvider no implementado aún")


def get_provider(name: str | None = None) -> WhatsAppProvider:
    """Factory del proveedor según settings.WHATSAPP_PROVIDER."""
    provider = (name or settings.WHATSAPP_PROVIDER).lower()
    if provider == "mock":
        return MockWhatsAppProvider()
    if provider == "twilio":
        return TwilioWhatsAppProvider()
    if provider == "meta":
        return MetaWhatsAppProvider()
    raise ValueError(f"Proveedor de WhatsApp desconocido: {provider}")
