"""Schemas del módulo de productos (FASE 02)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from app.modules.products.domain.models import Product
from pydantic import BaseModel, Field, field_validator


class AttributePair(BaseModel):
    attribute: str = Field(..., min_length=1)
    value: str = Field(..., min_length=1)
    data_type: str = "text"
    unit: str | None = None


class SerialCreate(BaseModel):
    serial_number: str = Field(..., min_length=1, max_length=200)
    imei: str | None = Field(default=None, max_length=50)
    imei2: str | None = Field(default=None, max_length=50)
    mac_address: str | None = Field(default=None, max_length=50)
    status: str = "AVAILABLE"
    notes: str | None = None


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    barcode: str | None = Field(default=None, max_length=100)
    description: str | None = None
    short_description: str | None = None
    brand_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    cost_price: Decimal = Field(default=Decimal("0"), ge=0)
    sale_price: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field("PEN", min_length=3, max_length=3)
    price_rule: str = "MANUAL"
    published: bool = False
    stock_minimum: int = Field(default=0, ge=0)
    is_serialized: bool = False
    weight_kg: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None
    attribute_links: list[AttributePair] = Field(default_factory=list)
    serials: list[SerialCreate] = Field(default_factory=list)

    _upper_currency = field_validator("currency")(lambda v: v.upper())


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    barcode: str | None = Field(default=None, max_length=100)
    description: str | None = None
    short_description: str | None = None
    brand_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    cost_price: Decimal | None = Field(default=None, ge=0)
    sale_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    price_rule: str | None = None
    stock_minimum: int | None = Field(default=None, ge=0)
    is_serialized: bool | None = None
    weight_kg: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class AttributeLinkResponse(BaseModel):
    attribute: str
    data_type: str
    unit: str | None
    value: str

    @classmethod
    def from_link(cls, link) -> AttributeLinkResponse:
        return cls(
            attribute=link.attribute_value.attribute.name,
            data_type=link.attribute_value.attribute.data_type,
            unit=link.attribute_value.attribute.unit,
            value=link.attribute_value.value,
        )


class SerialResponse(BaseModel):
    id: uuid.UUID
    serial_number: str
    imei: str | None
    imei2: str | None
    mac_address: str | None
    status: str
    notes: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, unit) -> SerialResponse:
        return cls(
            id=unit.id,
            serial_number=unit.serial_number,
            imei=unit.imei,
            imei2=unit.imei2,
            mac_address=unit.mac_address,
            status=unit.status,
            notes=unit.notes,
            created_at=unit.created_at,
        )


class OfferResponse(BaseModel):
    id: uuid.UUID
    normal_price: Decimal
    offer_price: Decimal
    start_at: datetime
    end_at: datetime
    active: bool
    created_at: datetime


class ProductImageResponse(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    display_order: int
    is_primary: bool
    url: str | None = None

    @classmethod
    def from_model(cls, image, url: str | None = None) -> ProductImageResponse:
        return cls(
            id=image.id,
            file_id=image.file_id,
            display_order=image.display_order,
            is_primary=image.is_primary,
            url=url,
        )


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    barcode: str | None
    name: str
    slug: str
    description: str | None
    short_description: str | None
    brand_id: uuid.UUID | None
    brand_name: str | None = None
    category_id: uuid.UUID | None
    category_name: str | None = None
    cost_price: Decimal
    sale_price: Decimal
    currency: str
    price_rule: str
    active: bool
    published: bool
    stock_minimum: int
    is_serialized: bool
    weight_kg: Decimal | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    attributes: list[AttributeLinkResponse] = Field(default_factory=list)
    serials: list[SerialResponse] = Field(default_factory=list)
    offers: list[OfferResponse] = Field(default_factory=list)
    images: list[ProductImageResponse] = Field(default_factory=list)
    current_price: Decimal | None = None
    current_currency: str | None = None

    @classmethod
    def from_product(
        cls, product: Product, include_cost: bool = True
    ) -> ProductResponse:
        attributes = [AttributeLinkResponse.from_link(link) for link in product.attribute_links]
        serials = [SerialResponse.from_model(s) for s in product.serials]
        offers = [
            OfferResponse(
                id=o.id,
                normal_price=o.normal_price,
                offer_price=o.offer_price,
                start_at=o.start_at,
                end_at=o.end_at,
                active=o.active,
                created_at=o.created_at,
            )
            for o in product.offers
        ]
        images = [ProductImageResponse.from_model(i) for i in product.images]
        return cls(
            id=product.id,
            sku=product.sku,
            barcode=product.barcode,
            name=product.name,
            slug=product.slug,
            description=product.description,
            short_description=product.short_description,
            brand_id=product.brand_id,
            brand_name=product.brand.name if product.brand else None,
            category_id=product.category_id,
            category_name=product.category.name if product.category else None,
            cost_price=product.cost_price if include_cost else Decimal("0"),
            sale_price=product.sale_price,
            currency=product.currency,
            price_rule=product.price_rule,
            active=product.active,
            published=product.published,
            stock_minimum=product.stock_minimum,
            is_serialized=product.is_serialized,
            weight_kg=product.weight_kg,
            notes=product.notes,
            created_at=product.created_at,
            updated_at=product.updated_at,
            attributes=attributes,
            serials=serials,
            offers=offers,
            images=images,
        )


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int


class OfferCreate(BaseModel):
    normal_price: Decimal = Field(..., gt=0)
    offer_price: Decimal = Field(..., gt=0)
    start_at: datetime
    end_at: datetime


class AssignAttributesRequest(BaseModel):
    attributes: list[AttributePair] = Field(default_factory=list)
