"""Servicio de clientes (#F04-21)."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.modules.audit.application.service import log
from app.modules.customers.application.schemas import CustomerCreate, CustomerUpdate
from app.modules.customers.domain.models import Customer
from app.modules.customers.infrastructure import repository
from app.modules.users.domain.models import User
from sqlalchemy.ext.asyncio import AsyncSession


async def create_customer(
    db: AsyncSession, *, data: CustomerCreate, created_by: User
) -> Customer:
    if data.dni:
        existing = await repository.get_by_dni(db, data.dni)
        if existing is not None:
            raise ConflictError(f"Ya existe un cliente con DNI {data.dni}")
    if data.ruc:
        existing = await repository.get_by_ruc(db, data.ruc)
        if existing is not None:
            raise ConflictError(f"Ya existe un cliente con RUC {data.ruc}")

    if data.is_blocked and not (data.block_reason and data.block_reason.strip()):
        raise ValidationError("Debe indicar motivo de bloqueo")

    customer = Customer(
        user_id=None,
        type=data.type,
        first_name=data.first_name,
        last_name=data.last_name,
        razon_social=data.razon_social,
        dni=data.dni,
        ruc=data.ruc,
        phone=data.phone,
        phone_whatsapp=data.phone_whatsapp,
        email=data.email,
        address=data.address,
        district=data.district,
        city=data.city,
        credit_limit=data.credit_limit,
        is_blocked=data.is_blocked,
        block_reason=data.block_reason if data.is_blocked else None,
        is_frequent=data.is_frequent,
        notes=data.notes,
        active=data.active,
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    await log(
        action="CREATE_CUSTOMER",
        module="customers",
        user_id=created_by.id,
        entity_type="Customer",
        entity_id=customer.id,
        new_values={
            "dni": customer.dni,
            "ruc": customer.ruc,
            "razon_social": customer.razon_social,
            "type": customer.type,
        },
    )
    return customer


async def update_customer(
    db: AsyncSession,
    *,
    customer_id: uuid.UUID,
    data: CustomerUpdate,
    updated_by: User,
) -> Customer:
    customer = await repository.get_by_id(db, customer_id)
    if customer is None:
        raise NotFoundError("Cliente no encontrado")

    payload = data.model_dump(exclude_unset=True)

    # Bloqueo: validaciones de transición
    new_is_blocked = payload.get("is_blocked", customer.is_blocked)
    new_block_reason = payload.get("block_reason", customer.block_reason)

    if new_is_blocked and not (new_block_reason and str(new_block_reason).strip()):
        raise ValidationError("Debe indicar block_reason para bloquear al cliente")

    # Si desbloquea, limpiar motivo automáticamente si no se provee nuevo
    if new_is_blocked is False and "block_reason" not in payload:
        payload["block_reason"] = None

    # Unicidad DNI / RUC si cambian
    if "dni" in payload and payload["dni"] is not None:
        dni = payload["dni"]
        if dni != customer.dni:
            existing = await repository.get_by_dni(db, dni)
            if existing is not None and existing.id != customer_id:
                raise ConflictError(f"Ya existe un cliente con DNI {dni}")
    if "ruc" in payload and payload["ruc"] is not None:
        ruc = payload["ruc"]
        if ruc != customer.ruc:
            existing = await repository.get_by_ruc(db, ruc)
            if existing is not None and existing.id != customer_id:
                raise ConflictError(f"Ya existe un cliente con RUC {ruc}")

    # Normalizar type a mayúsculas si viene
    if "type" in payload and payload["type"] is not None:
        payload["type"] = str(payload["type"]).upper()

    old_values = {
        "type": customer.type,
        "is_blocked": customer.is_blocked,
        "active": customer.active,
    }

    for field, value in payload.items():
        setattr(customer, field, value)

    await db.commit()
    await db.refresh(customer)
    await log(
        action="UPDATE_CUSTOMER",
        module="customers",
        user_id=updated_by.id,
        entity_type="Customer",
        entity_id=customer.id,
        old_values=old_values,
        new_values={
            "type": customer.type,
            "is_blocked": customer.is_blocked,
            "active": customer.active,
        },
    )
    return customer
