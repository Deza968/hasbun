"""Modelos del módulo de productos (#F02-05, #F02-07, #F02-08, #F02-11)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.database.base import Base, BaseModel
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.modules.attributes.domain.models import ProductAttributeValue
    from app.modules.brands.domain.models import Brand
    from app.modules.categories.domain.models import Category
    from app.modules.files.domain.models import FileObject
    from app.modules.users.domain.models import User


class Product(BaseModel, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="cost_price_non_negative"),
        CheckConstraint("sale_price >= 0", name="sale_price_non_negative"),
    )

    sku: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    barcode: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(280), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    price_rule: Mapped[str] = mapped_column(String(30), nullable=False, default="MANUAL")
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_minimum: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped[Brand | None] = relationship(
        "Brand", foreign_keys=[brand_id], lazy="selectin"
    )
    category: Mapped[Category | None] = relationship(
        "Category", foreign_keys=[category_id], lazy="selectin"
    )
    attribute_links: Mapped[list[ProductAttributeValue]] = relationship(
        "ProductAttributeValue",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    serials: Mapped[list[SerializedUnit]] = relationship(
        "SerializedUnit",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    offers: Mapped[list[ProductOffer]] = relationship(
        "ProductOffer",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    images: Mapped[list[ProductImage]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ProductImage.display_order",
    )


class SerializedUnit(BaseModel, Base):
    """Unidad serializada de un producto (#F02-07)."""

    __tablename__ = "serialized_units"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    serial_number: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    imei: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    imei2: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="AVAILABLE", index=True
    )
    # FK → PurchaseItem (FASE 03). Guardado como UUID sin constraint para no
    # bloquear esta fase.
    purchase_item_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[Product] = relationship(
        "Product", back_populates="serials", lazy="selectin"
    )


class ProductOffer(BaseModel, Base):
    """Oferta temporal de un producto (#F02-08)."""

    __tablename__ = "product_offers"
    __table_args__ = (
        CheckConstraint("offer_price > 0", name="offer_price_positive"),
        CheckConstraint("offer_price < normal_price", name="offer_lt_normal"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    normal_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    offer_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    product: Mapped[Product] = relationship(
        "Product", back_populates="offers", lazy="selectin"
    )
    creator: Mapped[User | None] = relationship(
        "User", foreign_keys=[created_by], lazy="selectin"
    )


class ProductImage(BaseModel, Base):
    """Imagen de un producto (#F02-11)."""

    __tablename__ = "product_images"
    __table_args__ = (
        CheckConstraint("display_order >= 0", name="order_non_negative"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("file_objects.id", ondelete="RESTRICT"), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship(
        "Product", back_populates="images", lazy="selectin"
    )
    file: Mapped[FileObject] = relationship("FileObject", lazy="selectin")


class SkuSequence(Base):
    """Secuencia por prefijo para el generador transaccional de SKU (#F02-06)."""

    __tablename__ = "sku_sequences"

    prefix: Mapped[str] = mapped_column(String(10), primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
