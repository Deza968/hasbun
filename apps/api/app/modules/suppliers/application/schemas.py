"""Schemas del módulo de proveedores (#F03-07)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.modules.suppliers.domain.models import Supplier
from pydantic import BaseModel, Field, field_validator


class SupplierCreate(BaseModel):
    razon_social: str = Field(..., min_length=2, max_length=255)
    ruc: str | None = Field(default=None, max_length=11)
    nombre_comercial: str | None = Field(default=None, max_length=255)
    contacto_nombre: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    telefono_whatsapp: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    direccion: str | None = None
    ciudad: str | None = Field(default=None, max_length=120)
    notes: str | None = None

    @field_validator("ruc")
    @classmethod
    def normalize_ruc(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not v.isdigit():
            raise ValueError("El RUC debe contener solo dígitos")
        return v


class SupplierUpdate(BaseModel):
    razon_social: str | None = Field(default=None, min_length=2, max_length=255)
    ruc: str | None = Field(default=None, max_length=11)
    nombre_comercial: str | None = Field(default=None, max_length=255)
    contacto_nombre: str | None = Field(default=None, max_length=255)
    telefono: str | None = Field(default=None, max_length=50)
    telefono_whatsapp: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    direccion: str | None = None
    ciudad: str | None = Field(default=None, max_length=120)
    notes: str | None = None


class SupplierResponse(BaseModel):
    id: uuid.UUID
    razon_social: str
    ruc: str | None
    nombre_comercial: str | None
    contacto_nombre: str | None
    telefono: str | None
    telefono_whatsapp: str | None
    email: str | None
    direccion: str | None
    ciudad: str | None
    active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, supplier: Supplier) -> SupplierResponse:
        return cls(
            id=supplier.id,
            razon_social=supplier.razon_social,
            ruc=supplier.ruc,
            nombre_comercial=supplier.nombre_comercial,
            contacto_nombre=supplier.contacto_nombre,
            telefono=supplier.telefono,
            telefono_whatsapp=supplier.telefono_whatsapp,
            email=supplier.email,
            direccion=supplier.direccion,
            ciudad=supplier.ciudad,
            active=supplier.active,
            notes=supplier.notes,
            created_at=supplier.created_at,
            updated_at=supplier.updated_at,
        )


class SupplierListResponse(BaseModel):
    items: list[SupplierResponse]
    total: int
