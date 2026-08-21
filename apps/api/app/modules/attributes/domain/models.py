"""Modelos del sistema de atributos dinámicos (#F02-04)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.products.domain.models import Product


class Attribute(BaseModel, Base):
    """Definición de un atributo (RAM, SSD, CPU, Color...)."""

    __tablename__ = "attributes"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    values: Mapped[list[AttributeValue]] = relationship(
        "AttributeValue",
        back_populates="attribute",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AttributeValue(BaseModel, Base):
    """Valor concreto de un atributo (ej: "8GB" en RAM)."""

    __tablename__ = "attribute_values"
    __table_args__ = (
        UniqueConstraint(
            "attribute_id", "value", name="uq_attribute_value_attribute_value"
        ),
    )

    attribute_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(200), nullable=False)

    attribute: Mapped[Attribute] = relationship(
        "Attribute", back_populates="values", lazy="selectin"
    )
    product_links: Mapped[list[ProductAttributeValue]] = relationship(
        "ProductAttributeValue",
        back_populates="attribute_value",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProductAttributeValue(Base):
    """Asignación de un valor de atributo a un producto."""

    __tablename__ = "product_attribute_values"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    attribute_value_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attribute_values.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )

    attribute_value: Mapped[AttributeValue] = relationship(
        "AttributeValue", back_populates="product_links", lazy="selectin"
    )
    product: Mapped[Product] = relationship(
        "Product", back_populates="attribute_links", lazy="selectin"
    )
