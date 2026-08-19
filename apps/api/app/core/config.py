"""Configuración central de la aplicación.

Usa pydantic-settings. Nunca hardcodear valores de configuración.
Toda variable requerida debe estar documentada en .env.example.
"""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global del sistema Hasbun."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Entorno
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Base de datos
    DATABASE_URL: str
    DATABASE_URL_TEST: str | None = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Seguridad / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # Almacenamiento S3 / MinIO
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = "hasbun"
    S3_REGION: str = "us-east-1"

    # WhatsApp
    WHATSAPP_PROVIDER: str = "mock"
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_ID: str = ""
    WHATSAPP_MOCK_FAIL_RATE: float = 0.0

    # Tipo de cambio
    EXCHANGE_RATE_PROVIDER: str = "mock"
    MOCK_EXCHANGE_RATE_USD_PEN: float = 3.75

    # Cifrado de credenciales de equipos (reparaciones)
    CREDENTIAL_ENCRYPTION_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"


@lru_cache
def get_settings() -> Settings:
    """Singleton de settings. Valida al arrancar si faltan variables requeridas."""
    return Settings()


settings = get_settings()
