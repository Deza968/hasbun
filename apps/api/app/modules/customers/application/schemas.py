"""Schemas del módulo de clientes (#F04-21)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.modules.customers.domain.models import Customer
from pydantic import BaseModel, Field, field_validator, model_validator


class CustomerCreate(BaseModel):
    """Payload para crear un cliente."""

    type: str = Field(default="PERSON", max_length=20, description="PERSON | COMPANY")
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    razon_social: str | None = Field(default=None, max_length=255)
    dni: str | None = Field(default=None, max_length=8)
    ruc: str | None = Field(default=None, max_length=11)
    phone: str | None = Field(default=None, max_length=50)
    phone_whatsapp: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    district: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)
    is_blocked: bool = False
    block_reason: str | None = None
    is_frequent: bool = False
    notes: str | None = None
    active: bool = True

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in ("PERSON", "COMPANY"):
            raise ValueError("type debe ser PERSON o COMPANY")
        return v

    @field_validator("dni")
    @classmethod
    def validate_dni(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.isdigit():
            raise ValueError("El DNI debe contener solo dígitos")
        if len(v) != 8:
            raise ValueError("El DNI debe tener 8 dígitos")
        return v

    @field_validator("ruc")
    @classmethod
    def validate_ruc(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.isdigit():
            raise ValueError("El RUC debe contener solo dígitos")
        if len(v) != 11:
            raise ValueError("El RUC debe tener 11 dígitos")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if "@" not in v:
            raise ValueError("Email inválido")
        return v.lower()

    @field_validator("first_name", "last_name", "razon_social", "phone", "phone_whatsapp")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def validate_block_and_identity(self) -> CustomerCreate:
        if self.is_blocked and not (self.block_reason and self.block_reason.strip()):
            raise ValueError("Debe indicar block_reason cuando is_blocked es True")
        if self.type == "COMPANY" and not (self.razon_social and self.razon_social.strip()):
            # permitir crear COMPANY sin razon_social, pero advertencia no bloqueante
            pass
        if self.type == "PERSON" and not (
            (self.first_name and self.first_name.strip())
            or (self.razon_social and self.razon_social.strip())
        ):
            pass
        if self.dni and self.ruc:
            # ambos permitidos pero validar que no sean inconsistentes
            pass
        return self


class CustomerUpdate(BaseModel):
    """Payload para actualizar un cliente (todos los campos opcionales)."""

    type: str | None = Field(default=None, max_length=20)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    razon_social: str | None = Field(default=None, max_length=255)
    dni: str | None = Field(default=None, max_length=8)
    ruc: str | None = Field(default=None, max_length=11)
    phone: str | None = Field(default=None, max_length=50)
    phone_whatsapp: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    address: str | None = None
    district: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    credit_limit: Decimal | None = Field(default=None, ge=0)
    is_blocked: bool | None = None
    block_reason: str | None = None
    is_frequent: bool | None = None
    notes: str | None = None
    active: bool | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if v not in ("PERSON", "COMPANY"):
            raise ValueError("type debe ser PERSON o COMPANY")
        return v

    @field_validator("dni")
    @classmethod
    def validate_dni(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.isdigit():
            raise ValueError("El DNI debe contener solo dígitos")
        if len(v) != 8:
            raise ValueError("El DNI debe tener 8 dígitos")
        return v

    @field_validator("ruc")
    @classmethod
    def validate_ruc(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.isdigit():
            raise ValueError("El RUC debe contener solo dígitos")
        if len(v) != 11:
            raise ValueError("El RUC debe tener 11 dígitos")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if "@" not in v:
            raise ValueError("Email inválido")
        return v.lower()

    @model_validator(mode="after")
    def validate_block(self) -> CustomerUpdate:
        if self.is_blocked is True and self.block_reason is not None:
            if not self.block_reason.strip():
                raise ValueError("Debe indicar block_reason cuando is_blocked es True")
        return self


class CustomerResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    type: str
    first_name: str | None
    last_name: str | None
    razon_social: str | None
    dni: str | None
    ruc: str | None
    phone: str | None
    phone_whatsapp: str | None
    email: str | None
    address: str | None
    district: str | None
    city: str | None
    credit_limit: Decimal
    is_blocked: bool
    block_reason: str | None
    is_frequent: bool
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, customer: Customer) -> CustomerResponse:
        return cls(
            id=customer.id,
            user_id=customer.user_id,
            type=customer.type,
            first_name=customer.first_name,
            last_name=customer.last_name,
            razon_social=customer.razon_social,
            dni=customer.dni,
            ruc=customer.ruc,
            phone=customer.phone,
            phone_whatsapp=customer.phone_whatsapp,
            email=customer.email,
            address=customer.address,
            district=customer.district,
            city=customer.city,
            credit_limit=customer.credit_limit,
            is_blocked=customer.is_blocked,
            block_reason=customer.block_reason,
            is_frequent=customer.is_frequent,
            notes=customer.notes,
            active=customer.active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
        )


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
