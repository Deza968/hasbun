"""Schemas del catálogo de productos."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.modules.products.domain.models import AttributeDataType, PriceRule, SerialUnitStatus
from pydantic import BaseModel, Field, field_validator

# ---------- Atributos ----------

class AttributeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    data_type: AttributeDataType = AttributeDataType.text
    unit: str | None = Field(default=None, max_length=30)


class AttributeValueCreate(BaseModel):
    value: str = Field(..., min_length=1, max_length=255)


class AttributeValueResponse(BaseModel):
    id: uuid.UUID
    attribute_id: uuid.UUID
    value: str


class AttributeResponse(BaseModel):
    id: uuid.UUID
    name: str
    data_type: AttributeDataType
    unit: str | None = None
    values: list[AttributeValueResponse] = []


# ---------- Productos ----------

class ProductAttributeInput(BaseModel):
    attribute_id: uuid.UUID
    value: str


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    barcode: str | None = Field(default=None, max_length=50)
    description: str | None = None
    short_description: str | None = None
    brand_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    cost_price: Decimal = Field(..., ge=0)
    sale_price: Decimal = Field(..., ge=0)
    currency: str = Field(default="PEN", pattern="^(PEN|USD)$")
    price_rule: PriceRule = PriceRule.FIXED_PEN
    stock_minimum: int = Field(default=0, ge=0)
    is_serialized: bool = False
    weight_kg: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None
    attributes: list[ProductAttributeInput] = Field(default_factory=list)

    @field_validator("sale_price")
    @classmethod
    def _sale_positive(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("El precio de venta debe ser mayor a 0")
        return value


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    barcode: str | None = Field(default=None, max_length=50)
    description: str | None = None
    short_description: str | None = None
    brand_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    cost_price: Decimal | None = Field(default=None, ge=0)
    sale_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern="^(PEN|USD)$")
    price_rule: PriceRule | None = None
    stock_minimum: int | None = Field(default=None, ge=0)
    is_serialized: bool | None = None
    weight_kg: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None
    active: bool | None = None


class ProductAttributeResponse(BaseModel):
    attribute_id: uuid.UUID
    attribute_name: str
    value: str
    value_id: uuid.UUID


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    display_order: int
    is_primary: bool
    url: str | None = None


class ProductOfferResponse(BaseModel):
    id: uuid.UUID
    normal_price: Decimal
    offer_price: Decimal
    start_at: datetime
    end_at: datetime
    active: bool


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    barcode: str | None = None
    name: str
    slug: str
    description: str | None = None
    short_description: str | None = None
    brand_id: uuid.UUID | None = None
    brand_name: str | None = None
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    cost_price: Decimal
    sale_price: Decimal
    currency: str
    price_rule: PriceRule
    current_price: Decimal
    active: bool
    published: bool
    stock_minimum: int
    is_serialized: bool
    weight_kg: Decimal | None = None
    notes: str | None = None
    attributes: list[ProductAttributeResponse] = []
    images: list[ProductImageResponse] = []
    active_offer: ProductOfferResponse | None = None
    serials_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int


class PublicProductResponse(BaseModel):
    """Versión pública del producto (tienda): sin costos ni datos internos."""

    id: uuid.UUID
    sku: str
    name: str
    slug: str
    description: str | None = None
    short_description: str | None = None
    brand_id: uuid.UUID | None = None
    brand_name: str | None = None
    category_id: uuid.UUID | None = None
    category_name: str | None = None
    sale_price: Decimal
    currency: str
    current_price: Decimal
    weight_kg: Decimal | None = None
    attributes: list[ProductAttributeResponse] = []
    images: list[ProductImageResponse] = []
    active_offer: ProductOfferResponse | None = None
    serials_count: int = 0


class PublicProductListResponse(BaseModel):
    items: list[PublicProductResponse]
    total: int


# ---------- Seriales ----------

class SerializedUnitCreate(BaseModel):
    serial_number: str = Field(..., min_length=1, max_length=100)
    imei: str | None = Field(default=None, max_length=30)
    imei2: str | None = Field(default=None, max_length=30)
    mac_address: str | None = Field(default=None, max_length=30)
    notes: str | None = None


class SerializedUnitUpdate(BaseModel):
    status: SerialUnitStatus
    notes: str | None = None


class SerializedUnitResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    serial_number: str
    imei: str | None = None
    imei2: str | None = None
    mac_address: str | None = None
    status: SerialUnitStatus
    notes: str | None = None
    created_at: datetime


# ---------- Ofertas ----------

class ProductOfferCreate(BaseModel):
    normal_price: Decimal = Field(..., gt=0)
    offer_price: Decimal = Field(..., gt=0)
    start_at: datetime
    end_at: datetime

    @field_validator("offer_price")
    @classmethod
    def _offer_less_than_normal(cls, value: Decimal, info) -> Decimal:
        normal = info.data.get("normal_price")
        if normal is not None and value >= normal:
            raise ValueError("El precio de oferta debe ser menor al precio normal")
        return value

    @field_validator("end_at")
    @classmethod
    def _end_after_start(cls, value: datetime, info) -> datetime:
        start = info.data.get("start_at")
        if start is not None and value <= start:
            raise ValueError("end_at debe ser posterior a start_at")
        return value
