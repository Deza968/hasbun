"""Router de productos, seriales, ofertas e imágenes (FASE 02)."""

from __future__ import annotations

import uuid
from typing import Annotated

from app.core.dependencies import DbSession, get_current_user, require_permission
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.modules.products.application import service
from app.modules.products.application.schemas import (
    AssignAttributesRequest,
    OfferCreate,
    OfferResponse,
    ProductCreate,
    ProductImageResponse,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    SerialCreate,
    SerialResponse,
)
from app.modules.products.domain.models import (
    SerializedUnit,
)
from app.modules.products.infrastructure import repository
from app.modules.users.domain.models import User
from fastapi import APIRouter, Depends, Query, Request

router = APIRouter(tags=["products"])

ManageProducts = Annotated[User, Depends(require_permission("productos.editar"))]
PublishProducts = Annotated[User, Depends(require_permission("productos.publicar"))]
ViewProducts = Annotated[User, Depends(require_permission("productos.ver"))]


async def _current_user_can_manage(request: Request, db) -> User:
    """Autentica opcionalmente. 401 si no hay sesión."""
    user = await get_current_user(request, db)
    return user


@router.get("/products", response_model=ProductListResponse)
async def list_products(
    request: Request,
    db: DbSession,
    search: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    brand_id: uuid.UUID | None = Query(None),
    active: bool | None = Query(None),
    published: bool | None = Query(None),
    admin: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> ProductListResponse:
    """Lista productos con filtros y paginación.

    Modo público (`admin=false`): solo published+active, sin costos ni seriales.
    Modo admin (`admin=true`): requiere permiso `productos.ver` e incluye costos.
    """
    include_cost = False
    if admin:
        actor = await _current_user_can_manage(request, db)
        if not (
            actor.is_superuser
            or "productos.ver" in await _perms_of(db, actor)
            or "*" in await _perms_of(db, actor)
        ):
            raise AuthorizationError("Permiso requerido: productos.ver")

    items, total = await repository.list_products(
        db,
        search=search,
        category_id=category_id,
        brand_id=brand_id,
        active=active if admin else True,
        published=published if admin else True,
        page=page,
        per_page=per_page,
    )
    result = []
    for product in items:
        resp = ProductResponse.from_product(product, include_cost=include_cost and admin)
        price_info = await service.get_current_price(db, product)
        resp.current_price = price_info["price"]  # type: ignore[assignment]
        resp.current_currency = price_info["currency"]  # type: ignore[assignment]
        result.append(resp)
    return ProductListResponse(items=result, total=total)


async def _perms_of(db, actor: User) -> list[str]:
    from app.modules.auth.application.service import get_user_permissions

    return await get_user_permissions(db, actor)


@router.get("/products/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    db: DbSession,
    _: ViewProducts,
) -> ProductResponse:
    """Busca por SKU (solo admin)."""
    product = await repository.get_by_sku(db, sku)
    if product is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")
    resp = ProductResponse.from_product(product, include_cost=True)
    price_info = await service.get_current_price(db, product)
    resp.current_price = price_info["price"]  # type: ignore[assignment]
    resp.current_currency = price_info["currency"]  # type: ignore[assignment]
    return resp


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    request: Request,
    db: DbSession,
) -> ProductResponse:
    """Detalle. Público solo si loose published y active."""
    product = await repository.get_by_id(db, product_id)
    if product is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")

    include_cost = False
    try:
        actor = await _current_user_can_manage(request, db)
        perms = await _perms_of(db, actor)
        include_cost = actor.is_superuser or "productos.ver" in perms or "*" in perms
    except AuthenticationError:
        actor = None

    if not product.published and not include_cost:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")

    resp = ProductResponse.from_product(product, include_cost=include_cost)
    price_info = await service.get_current_price(db, product)
    resp.current_price = price_info["price"]  # type: ignore[assignment]
    resp.current_currency = price_info["currency"]  # type: ignore[assignment]
    return resp


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    db: DbSession,
    actor: ManageProducts,
) -> ProductResponse:
    """Crea un producto con SKU automático (solo OWNER)."""
    product = await service.create_product(db, data=body, created_by=actor)
    price_info = await service.get_current_price(db, product)
    resp = ProductResponse.from_product(product, include_cost=True)
    resp.current_price = price_info["price"]  # type: ignore[assignment]
    resp.current_currency = price_info["currency"]  # type: ignore[assignment]
    return resp


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    db: DbSession,
    actor: ManageProducts,
) -> ProductResponse:
    product = await service.update_product(
        db, product_id=product_id, data=body, updated_by=actor
    )
    resp = ProductResponse.from_product(product, include_cost=True)
    price_info = await service.get_current_price(db, product)
    resp.current_price = price_info["price"]  # type: ignore[assignment]
    resp.current_currency = price_info["currency"]  # type: ignore[assignment]
    return resp


@router.delete("/products/{product_id}", response_model=ProductResponse)
async def deactivate_product(
    product_id: uuid.UUID,
    db: DbSession,
    actor: ManageProducts,
) -> ProductResponse:
    product = await service.deactivate_product(
        db, product_id=product_id, deactivated_by=actor
    )
    return ProductResponse.from_product(product, include_cost=True)


@router.post("/products/{product_id}/publish", response_model=ProductResponse)
async def publish_product(
    product_id: uuid.UUID,
    db: DbSession,
    actor: PublishProducts,
) -> ProductResponse:
    product = await service.publish_product(
        db, product_id=product_id, published=True, user=actor
    )
    return ProductResponse.from_product(product, include_cost=True)


@router.post("/products/{product_id}/unpublish", response_model=ProductResponse)
async def unpublish_product(
    product_id: uuid.UUID,
    db: DbSession,
    actor: PublishProducts,
) -> ProductResponse:
    product = await service.publish_product(
        db, product_id=product_id, published=False, user=actor
    )
    return ProductResponse.from_product(product, include_cost=True)


@router.post("/products/{product_id}/attributes", response_model=ProductResponse)
async def assign_attributes(
    product_id: uuid.UUID,
    body: AssignAttributesRequest,
    db: DbSession,
    actor: ManageProducts,
) -> ProductResponse:
    product = await service.assign_attributes(
        db,
        product_id=product_id,
        pairs=[pair.model_dump() for pair in body.attributes],
        updated_by=actor,
    )
    return ProductResponse.from_product(product, include_cost=True)


@router.get("/products/{product_id}/serials", response_model=list[SerialResponse])
async def list_product_serials(
    product_id: uuid.UUID,
    db: DbSession,
    _: ViewProducts,
) -> list[SerialResponse]:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")
    return [SerialResponse.from_model(s) for s in product.serials]


@router.post("/products/{product_id}/serials", response_model=SerialResponse, status_code=201)
async def register_serial(
    product_id: uuid.UUID,
    body: SerialCreate,
    db: DbSession,
    actor: ManageProducts,
) -> SerialResponse:
    unit = await service.register_serial(
        db, product_id=product_id, data=body, user=actor
    )
    return SerialResponse.from_model(unit)


@router.get("/products/{product_id}/serials/{serial_id}", response_model=SerialResponse)
async def get_serial(
    product_id: uuid.UUID,
    serial_id: uuid.UUID,
    db: DbSession,
    _: ViewProducts,
) -> SerialResponse:
    unit = await db.get(SerializedUnit, serial_id)
    if unit is None or unit.product_id != product_id:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Serie no encontrada")
    return SerialResponse.from_model(unit)


@router.put("/products/{product_id}/serials/{serial_id}", response_model=SerialResponse)
async def update_serial(
    product_id: uuid.UUID,
    serial_id: uuid.UUID,
    body: SerialCreate,
    db: DbSession,
    actor: ManageProducts,
) -> SerialResponse:
    unit = await db.get(SerializedUnit, serial_id)
    if unit is None or unit.product_id != product_id:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Serie no encontrada")
    updated = await service.update_serial_status(
        db, serial_id=serial_id, status=body.status, user=actor
    )
    return SerialResponse.from_model(updated)


@router.get("/products/{product_id}/serials/{serial_id}/price")
async def serial_price_check(
    product_id: uuid.UUID,
    serial_id: uuid.UUID,
    db: DbSession,
) -> dict[str, object]:
    """Verificación de precio de un serial (omitido en esta fase)."""
    return {"product_id": str(product_id), "serial_id": str(serial_id), "price": None}


@router.post("/products/{product_id}/offers", response_model=OfferResponse, status_code=201)
async def create_offer(
    product_id: uuid.UUID,
    body: OfferCreate,
    db: DbSession,
    actor: ManageProducts,
) -> OfferResponse:
    offer = await service.create_offer(
        db, product_id=product_id, data=body, user=actor
    )
    return OfferResponse(
        id=offer.id,
        normal_price=offer.normal_price,
        offer_price=offer.offer_price,
        start_at=offer.start_at,
        end_at=offer.end_at,
        active=offer.active,
        created_at=offer.created_at,
    )


@router.get("/products/{product_id}/offers", response_model=list[OfferResponse])
async def list_offers(
    product_id: uuid.UUID,
    db: DbSession,
) -> list[OfferResponse]:
    product = await repository.get_by_id(db, product_id)
    if product is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")
    return [
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


@router.delete("/products/{product_id}/offers/{offer_id}", response_model=OfferResponse)
async def deactivate_offer(
    product_id: uuid.UUID,
    offer_id: uuid.UUID,
    db: DbSession,
    actor: ManageProducts,
) -> OfferResponse:
    offer = await service.deactivate_offer(db, offer_id=offer_id, user=actor)
    return OfferResponse(
        id=offer.id,
        normal_price=offer.normal_price,
        offer_price=offer.offer_price,
        start_at=offer.start_at,
        end_at=offer.end_at,
        active=offer.active,
        created_at=offer.created_at,
    )


@router.get("/products/{product_id}/images", response_model=list[ProductImageResponse])
async def list_product_images(
    product_id: uuid.UUID,
    db: DbSession,
) -> list[ProductImageResponse]:
    """Lista imágenes del producto (público si el producto es published)."""
    product = await repository.get_by_id(db, product_id)
    if product is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Producto no encontrado")
    images = product.images
    result: list[ProductImageResponse] = []
    for image in images:
        resp = ProductImageResponse.from_model(image)
        try:
            resp.url = await _file_url(db, image.file_id)
        except Exception:  # noqa: BLE001
            resp.url = None
        result.append(resp)
    return result


async def _file_url(db, file_id: uuid.UUID) -> str:
    from app.modules.files.application.service import get_file_url

    return await get_file_url(db, file_id=file_id)


@router.post("/products/{product_id}/images", response_model=ProductImageResponse, status_code=201)
async def add_product_image(
    product_id: uuid.UUID,
    db: DbSession,
    actor: ManageProducts,
    file_id: uuid.UUID = Query(..., description="FileObject id del archivo subido"),
) -> ProductImageResponse:
    image = await service.add_product_image(
        db, product_id=product_id, file_id=file_id, user=actor
    )
    return ProductImageResponse.from_model(image)


@router.put("/products/{product_id}/images/{image_id}/primary", response_model=ProductImageResponse)
async def mark_image_primary(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DbSession,
    actor: ManageProducts,
) -> ProductImageResponse:
    image = await service.mark_image_primary(db, image_id=image_id, user=actor)
    return ProductImageResponse.from_model(image)


@router.delete("/products/{product_id}/images/{image_id}")
async def remove_product_image(
    product_id: uuid.UUID,
    image_id: uuid.UUID,
    db: DbSession,
    actor: ManageProducts,
) -> dict[str, str]:
    await service.remove_product_image(db, image_id=image_id, user=actor)
    return {"message": "Imagen eliminada"}
