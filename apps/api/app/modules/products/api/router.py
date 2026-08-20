"""Router de productos, seriales y ofertas."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, require_permission
from app.modules.brands.infrastructure import repository as brands_repo
from app.modules.categories.infrastructure import repository as categories_repo
from app.modules.products.application.schemas import (
    ProductAttributeInput,
    ProductCreate,
    ProductListResponse,
    ProductOfferCreate,
    ProductOfferResponse,
    ProductResponse,
    ProductUpdate,
    PublicProductListResponse,
    PublicProductResponse,
    SerializedUnitCreate,
    SerializedUnitResponse,
    SerializedUnitUpdate,
)
from app.modules.products.application.service import (
    add_product_image,
    create_offer,
    create_product,
    deactivate_offer,
    deactivate_product,
    get_current_price,
    register_serial,
    remove_product_image,
    set_primary_image,
    set_product_attributes,
    set_published,
    update_product,
    update_serial_status,
)
from app.modules.products.domain.models import Product, ProductImage
from app.modules.products.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query, UploadFile

router = APIRouter(tags=["products"])

ViewProducts = Annotated[User, Depends(require_permission("productos.ver"))]
CreateProduct = Annotated[User, Depends(require_permission("productos.crear"))]
EditProduct = Annotated[User, Depends(require_permission("productos.editar"))]
EditCost = Annotated[User, Depends(require_permission("productos.editar_costo"))]
DeleteProduct = Annotated[User, Depends(require_permission("productos.eliminar"))]
PublishProduct = Annotated[User, Depends(require_permission("productos.publicar"))]


async def _to_response(db, product: Product) -> ProductResponse:
    brand_name = None
    if product.brand_id:
        brand = await brands_repo.get_by_id(db, product.brand_id)
        brand_name = brand.name if brand else None
    category_name = None
    if product.category_id:
        category = await categories_repo.get_by_id(db, product.category_id)
        category_name = category.name if category else None

    active_offer, current_price = await get_current_price(db, product)
    attributes = [
        {
            "attribute_id": av.attribute_id,
            "attribute_name": av.attribute.name,
            "value": av.value,
            "value_id": av.id,
        }
        for av in product.attribute_values
    ]
    images = [
        {
            "id": img.id,
            "file_id": img.file_id,
            "display_order": img.display_order,
            "is_primary": img.is_primary,
            "url": f"/api/v1/files/{img.file_id}/download",
        }
        for img in product.images
    ]
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        barcode=product.barcode,
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        brand_id=product.brand_id,
        brand_name=brand_name,
        category_id=product.category_id,
        category_name=category_name,
        cost_price=product.cost_price,
        sale_price=product.sale_price,
        currency=product.currency,
        price_rule=product.price_rule,
        current_price=current_price,
        active=product.active,
        published=product.published,
        stock_minimum=product.stock_minimum,
        is_serialized=product.is_serialized,
        weight_kg=product.weight_kg,
        notes=product.notes,
        attributes=attributes,
        images=images,
        active_offer=(
            ProductOfferResponse(
                id=active_offer.id,
                normal_price=active_offer.normal_price,
                offer_price=active_offer.offer_price,
                start_at=active_offer.start_at,
                end_at=active_offer.end_at,
                active=active_offer.active,
            )
            if active_offer
            else None
        ),
        serials_count=len(product.serials),
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


async def _to_public_response(db, product: Product) -> PublicProductResponse:
    brand_name = None
    if product.brand_id:
        brand = await brands_repo.get_by_id(db, product.brand_id)
        brand_name = brand.name if brand else None
    category_name = None
    if product.category_id:
        category = await categories_repo.get_by_id(db, product.category_id)
        category_name = category.name if category else None

    active_offer, current_price = await get_current_price(db, product)
    attributes = [
        {
            "attribute_id": av.attribute_id,
            "attribute_name": av.attribute.name,
            "value": av.value,
            "value_id": av.id,
        }
        for av in product.attribute_values
    ]
    images = [
        {
            "id": img.id,
            "file_id": img.file_id,
            "display_order": img.display_order,
            "is_primary": img.is_primary,
            "url": f"/api/v1/files/{img.file_id}/download",
        }
        for img in product.images
    ]
    return PublicProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        brand_id=product.brand_id,
        brand_name=brand_name,
        category_id=product.category_id,
        category_name=category_name,
        sale_price=product.sale_price,
        currency=product.currency,
        current_price=current_price,
        weight_kg=product.weight_kg,
        attributes=attributes,
        images=images,
        active_offer=(
            ProductOfferResponse(
                id=active_offer.id,
                normal_price=active_offer.normal_price,
                offer_price=active_offer.offer_price,
                start_at=active_offer.start_at,
                end_at=active_offer.end_at,
                active=active_offer.active,
            )
            if active_offer
            else None
        ),
        serials_count=len(product.serials),
    )


@router.get("/products", response_model=PublicProductListResponse)
async def list_products_public(
    db: DbSession,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    brand_id: uuid.UUID | None = None,
) -> PublicProductListResponse:
    """Lista catálogo público (solo productos activos y publicados)."""
    items, total = await repository.list_products(
        db,
        offset=offset,
        limit=limit,
        search=search,
        category_id=category_id,
        brand_id=brand_id,
        public=True,
    )
    return PublicProductListResponse(
        items=[await _to_public_response(db, p) for p in items], total=total
    )


@router.get("/products/admin", response_model=ProductListResponse)
async def list_products_admin(
    db: DbSession,
    _: ViewProducts,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    search: str | None = None,
    category_id: uuid.UUID | None = None,
    brand_id: uuid.UUID | None = None,
    active: bool | None = None,
    published: bool | None = None,
) -> ProductListResponse:
    """Lista productos con filtros y paginación (solo admin)."""
    items, total = await repository.list_products(
        db,
        offset=offset,
        limit=limit,
        search=search,
        category_id=category_id,
        brand_id=brand_id,
        active=active,
        published=published,
    )
    return ProductListResponse(
        items=[await _to_response(db, p) for p in items], total=total
    )


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product_endpoint(
    body: ProductCreate,
    db: DbSession,
    actor: CreateProduct,
) -> ProductResponse:
    """Crea un producto con SKU automático (solo OWNER)."""
    product = await create_product(db, data=body, created_by=actor)
    return await _to_response(db, product)


@router.get("/products/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: DbSession,
    _: ViewProducts,
) -> ProductResponse:
    """Busca un producto por SKU (admin)."""
    product = await repository.get_by_sku(db, sku)
    if product is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")
    return await _to_response(db, product)


@router.get("/products/{product_id}", response_model=PublicProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: DbSession,
) -> PublicProductResponse:
    """Detalle de un producto (público si published)."""
    from app.core.exceptions import NotFoundError

    product = await repository.get_by_id(db, product_id)
    if product is None or not (product.published and product.active):
        raise NotFoundError("Producto no encontrado")
    return await _to_public_response(db, product)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product_endpoint(
    product_id: uuid.UUID,
    body: ProductUpdate,
    db: DbSession,
    actor: EditProduct,
) -> ProductResponse:
    """Actualiza un producto (solo OWNER)."""
    product = await update_product(db, product_id=product_id, data=body, updated_by=actor)
    return await _to_response(db, product)


@router.post("/products/{product_id}/publish", response_model=ProductResponse)
async def publish_product_endpoint(
    product_id: uuid.UUID,
    db: DbSession,
    actor: PublishProduct,
) -> ProductResponse:
    """Publica un producto (solo OWNER)."""
    product = await set_published(db, product_id=product_id, published=True, actor=actor)
    return await _to_response(db, product)


@router.post("/products/{product_id}/unpublish", response_model=ProductResponse)
async def unpublish_product_endpoint(
    product_id: uuid.UUID,
    db: DbSession,
    actor: PublishProduct,
) -> ProductResponse:
    """Despublica un producto (solo OWNER)."""
    product = await set_published(db, product_id=product_id, published=False, actor=actor)
    return await _to_response(db, product)


@router.delete("/products/{product_id}", status_code=204)
async def deactivate_product_endpoint(
    product_id: uuid.UUID,
    db: DbSession,
    actor: DeleteProduct,
) -> None:
    """Desactiva un producto (solo OWNER)."""
    await deactivate_product(db, product_id=product_id, deactivated_by=actor)


@router.post("/products/{product_id}/attributes", response_model=ProductResponse)
async def set_product_attributes_endpoint(
    product_id: uuid.UUID,
    body: list[ProductAttributeInput],
    db: DbSession,
    actor: EditProduct,
) -> ProductResponse:
    """Asigna atributos a un producto (solo OWNER)."""
    product = await set_product_attributes(
        db, product_id=product_id, attributes=body, updated_by=actor
    )
    return await _to_response(db, product)


# ---------- Seriales ----------

@router.get("/products/{product_id}/serials", response_model=list[SerializedUnitResponse])
async def list_serials(
    product_id: uuid.UUID,
    db: DbSession,
    _: ViewProducts,
) -> list[SerializedUnitResponse]:
    """Lista los seriales de un producto (solo admin)."""
    units = await repository.list_serials(db, product_id=product_id)
    return [
        SerializedUnitResponse(
            id=u.id,
            product_id=u.product_id,
            serial_number=u.serial_number,
            imei=u.imei,
            imei2=u.imei2,
            mac_address=u.mac_address,
            status=u.status,
            notes=u.notes,
            created_at=u.created_at,
        )
        for u in units
    ]


@router.post(
    "/products/{product_id}/serials",
    response_model=SerializedUnitResponse,
    status_code=201,
)
async def register_serial_endpoint(
    product_id: uuid.UUID,
    body: SerializedUnitCreate,
    db: DbSession,
    actor: CreateProduct,
) -> SerializedUnitResponse:
    """Registra un serial para un producto serializado (solo OWNER)."""
    unit = await register_serial(db, product_id=product_id, data=body, created_by=actor)
    return SerializedUnitResponse(
        id=unit.id,
        product_id=unit.product_id,
        serial_number=unit.serial_number,
        imei=unit.imei,
        imei2=unit.imei2,
        mac_address=unit.mac_address,
        status=unit.status,
        notes=unit.notes,
        created_at=unit.created_at,
    )


@router.put("/products/{product_id}/serials/{serial_id}", response_model=SerializedUnitResponse)
async def update_serial_status_endpoint(
    product_id: uuid.UUID,
    serial_id: uuid.UUID,
    body: SerializedUnitUpdate,
    db: DbSession,
    actor: EditProduct,
) -> SerializedUnitResponse:
    """Actualiza el estado de un serial (con auditoría)."""
    unit = await update_serial_status(
        db,
        product_id=product_id,
        serial_id=serial_id,
        status=body.status,
        notes=body.notes,
        updated_by=actor,
    )
    return SerializedUnitResponse(
        id=unit.id,
        product_id=unit.product_id,
        serial_number=unit.serial_number,
        imei=unit.imei,
        imei2=unit.imei2,
        mac_address=unit.mac_address,
        status=unit.status,
        notes=unit.notes,
        created_at=unit.created_at,
    )


# ---------- Ofertas ----------

@router.get("/products/{product_id}/offers", response_model=list[ProductOfferResponse])
async def list_offers(
    product_id: uuid.UUID,
    db: DbSession,
) -> list[ProductOfferResponse]:
    """Lista las ofertas de un producto."""
    offers = await repository.list_offers(db, product_id=product_id)
    return [
        ProductOfferResponse(
            id=o.id,
            normal_price=o.normal_price,
            offer_price=o.offer_price,
            start_at=o.start_at,
            end_at=o.end_at,
            active=o.active,
        )
        for o in offers
    ]


@router.post("/products/{product_id}/offers", response_model=ProductOfferResponse, status_code=201)
async def create_offer_endpoint(
    product_id: uuid.UUID,
    body: ProductOfferCreate,
    db: DbSession,
    actor: CreateProduct,
) -> ProductOfferResponse:
    """Crea una oferta para un producto (solo OWNER)."""
    offer = await create_offer(db, product_id=product_id, data=body, created_by=actor)
    return ProductOfferResponse(
        id=offer.id,
        normal_price=offer.normal_price,
        offer_price=offer.offer_price,
        start_at=offer.start_at,
        end_at=offer.end_at,
        active=offer.active,
    )


@router.delete("/products/{product_id}/offers/{offer_id}", status_code=204)
async def deactivate_offer_endpoint(
    product_id: uuid.UUID,
    offer_id: uuid.UUID,
    db: DbSession,
    actor: CreateProduct,
) -> None:
    """Desactiva una oferta (solo OWNER)."""
    await deactivate_offer(db, product_id=product_id, offer_id=offer_id, actor=actor)


# ---------- Imágenes ----------

def _image_response(image: ProductImage) -> dict:
    return {
        "id": image.id,
        "file_id": image.file_id,
        "display_order": image.display_order,
        "is_primary": image.is_primary,
        "url": f"/api/v1/files/{image.file_id}/download",
    }


@router.post("/products/{product_id}/images", response_model=dict, status_code=201)
async def add_product_image_endpoint(
    product_id: uuid.UUID,
    file: UploadFile,
    db: DbSession,
    actor: EditProduct,
) -> dict:
    """Sube y asocia una imagen a un producto (solo OWNER)."""
    data = await file.read()
    try:
        filename = file.filename or "imagen"
    finally:
        await file.close()
    image = await add_product_image(
        db,
        product_id=product_id,
        data=data,
        filename=filename,
        mime_type=file.content_type,
        actor=actor,
    )
    return _image_response(image)


@router.post(
    "/products/{product_id}/images/{image_id}/primary",
    response_model=dict,
    status_code=200,
)
async def set_primary_image_endpoint(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DbSession,
    actor: EditProduct,
) -> dict:
    """Marca una imagen como principal (solo OWNER)."""
    await set_primary_image(db, product_id=product_id, image_id=image_id, actor=actor)
    return {"status": "ok"}


@router.delete("/products/{product_id}/images/{image_id}", status_code=204)
async def remove_product_image_endpoint(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DbSession,
    actor: EditProduct,
) -> None:
    """Elimina una imagen de un producto (solo OWNER)."""
    await remove_product_image(db, product_id=product_id, image_id=image_id, actor=actor)
