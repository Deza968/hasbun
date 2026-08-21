"""Modelo del módulo de proveedores (#F03-07)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.users.domain.models import User


class Supplier(BaseModel, Base):
    __tablename__ = "suppliers"

    razon_social: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ruc: Mapped[str | None] = mapped_column(String(11), unique=True, nullable=True)
    nombre_comercial: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contacto_nombre: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    telefono_whatsapp: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(120), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    creator: Mapped[User | None] = relationship("User", lazy="selectin")
