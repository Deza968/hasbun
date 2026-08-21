"""Servicio de proveedores (#F03-07)."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.audit.application.service import log
from app.modules.suppliers.domain.models import Supplier
from app.modules.suppliers.infrastructure import repository
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_supplier(
    db: AsyncSession, *, data, created_by: User
) -> Supplier:
    if data.ruc:
        existing = await repository.get_by_ruc(db, data.ruc)
        if existing is not None:
            raise ConflictError(f"Ya existe un proveedor con RUC {data.ruc}")
    supplier = Supplier(
        razon_social=data.razon_social,
        ruc=data.ruc,
        nombre_comercial=data.nombre_comercial,
        contacto_nombre=data.contacto_nombre,
        telefono=data.telefono,
        telefono_whatsapp=data.telefono_whatsapp,
        email=data.email,
        direccion=data.direccion,
        ciudad=data.ciudad,
        active=True,
        notes=data.notes,
        created_by=created_by.id,
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    await log(
        action="CREATE_SUPPLIER",
        module="suppliers",
        user_id=created_by.id,
        entity_type="Supplier",
        entity_id=supplier.id,
        new_values={"razon_social": supplier.razon_social, "ruc": supplier.ruc},
    )
    return supplier


async def update_supplier(
    db: AsyncSession, *, supplier_id: uuid.UUID, data, updated_by: User
) -> Supplier:
    supplier = await repository.get_by_id(db, supplier_id)
    if supplier is None:
        raise NotFoundError("Proveedor no encontrado")
    if data.ruc:
        existing = await repository.get_by_ruc(db, data.ruc)
        if existing is not None and existing.id != supplier_id:
            raise ConflictError(f"Ya existe un proveedor con RUC {data.ruc}")

    old_values = {"razon_social": supplier.razon_social}
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    await db.commit()
    await db.refresh(supplier)
    await log(
        action="UPDATE_SUPPLIER",
        module="suppliers",
        user_id=updated_by.id,
        entity_type="Supplier",
        entity_id=supplier.id,
        old_values=old_values,
        new_values={"razon_social": supplier.razon_social},
    )
    return supplier


async def deactivate_supplier(
    db: AsyncSession, *, supplier_id: uuid.UUID, user: User
) -> Supplier:
    supplier = await repository.get_by_id(db, supplier_id)
    if supplier is None:
        raise NotFoundError("Proveedor no encontrado")
    supplier.active = False
    await db.commit()
    await db.refresh(supplier)
    await log(
        action="DEACTIVATE_SUPPLIER",
        module="suppliers",
        user_id=user.id,
        entity_type="Supplier",
        entity_id=supplier.id,
        new_values={"active": False},
    )
    return supplier
