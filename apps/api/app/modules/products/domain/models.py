"""Modelos de dominio del catálogo de productos.

Incluye: Attribute, AttributeValue, Product, SkuSequence, SerializedUnit,
ProductOffer y ProductImage, más la tabla asociativa ProductAttributeValue.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from app.database.base import Base, BaseModel
from app.modules.files.domain.models import FileObject
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class AttributeDataType(enum.StrEnum):
    text = "text"
    number = "number"
    boolean = "boolean"
    list_ = "list"


class PriceRule(enum.StrEnum):
    FIXED_PEN = "FIXED_PEN"
    FIXED_USD = "FIXED_USD"
    USD_CONVERTED = "USD_CONVERTED"
    COST_USD_MARGIN = "COST_USD_MARGIN"
    MANUAL = "MANUAL"


class SerialUnitStatus(enum.StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    DELIVERED_ON_CREDIT = "DELIVERED_ON_CREDIT"
    SOLD = "SOLD"
    IN_REPAIR = "IN_REPAIR"
    RETURNED = "RETURNED"
    DAMAGED = "DAMAGED"


class Attribute(BaseModel, Base):
    __tablename__ = "attributes"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    data_type: Mapped[AttributeDataType] = mapped_column(
        Enum(AttributeDataType, name="attribute_data_type", native_enum=True),
        nullable=False,
        default=AttributeDataType.text,
    )
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)

    values: Mapped[list[AttributeValue]] = relationship(
        "AttributeValue",
        back_populates="attribute",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class AttributeValue(BaseModel, Base):
    __tablename__ = "attribute_values"
    __table_args__ = (
        Index(
            "uq_attribute_values_attribute_value",
            "attribute_id",
            "value",
            unique=True,
        ),
    )

    attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attributes.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    attribute: Mapped[Attribute] = relationship(
        "Attribute", back_populates="values", lazy="selectin"
    )
    products: Mapped[list[Product]] = relationship(
        "Product",
        secondary="product_attribute_values",
        back_populates="attribute_values",
        lazy="selectin",
    )


class Product(BaseModel, Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="cost_price_non_negative"),
        CheckConstraint("sale_price >= 0", name="sale_price_non_negative"),
    )

    sku: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    barcode: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(260), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    cost_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    price_rule: Mapped[PriceRule] = mapped_column(
        Enum(PriceRule, name="price_rule", native_enum=True),
        nullable=False,
        default=PriceRule.FIXED_PEN,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_minimum: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_serialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    attribute_values: Mapped[list[AttributeValue]] = relationship(
        "AttributeValue",
        secondary="product_attribute_values",
        back_populates="products",
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


class ProductAttributeValue(Base):
    __tablename__ = "product_attribute_values"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), primary_key=True
    )
    attribute_value_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("attribute_values.id", ondelete="CASCADE"),
        primary_key=True,
    )


class SkuSequence(Base):
    __tablename__ = "sku_sequences"

    prefix: Mapped[str] = mapped_column(String(10), primary_key=True)
    last_value: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)


class SerializedUnit(BaseModel, Base):
    __tablename__ = "serialized_units"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    serial_number: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    imei: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    imei2: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mac_address: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[SerialUnitStatus] = mapped_column(
        Enum(SerialUnitStatus, name="serial_unit_status", native_enum=True),
        nullable=False,
        default=SerialUnitStatus.AVAILABLE,
    )
    # FK a PurchaseItem llegará en FASE 03 (tabla purchases aún no existe)
    purchase_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    product: Mapped[Product] = relationship(
        "Product", back_populates="serials", lazy="selectin"
    )


class ProductOffer(BaseModel, Base):
    __tablename__ = "product_offers"
    __table_args__ = (
        CheckConstraint("offer_price < normal_price", name="offer_below_normal"),
        CheckConstraint("offer_price > 0", name="offer_positive"),
        CheckConstraint("end_at > start_at", name="end_after_start"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    normal_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    offer_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    product: Mapped[Product] = relationship(
        "Product", back_populates="offers", lazy="selectin"
    )


class ProductImage(BaseModel, Base):
    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("file_objects.id", ondelete="CASCADE"), nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    product: Mapped[Product] = relationship(
        "Product", back_populates="images", lazy="selectin"
    )
    file: Mapped[FileObject] = relationship("FileObject", lazy="selectin")
