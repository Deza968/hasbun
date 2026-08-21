"""Seed de 10 clientes ficticios (#F04-21)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.domain.models import Customer

CUSTOMERS: list[dict] = [
    {
        "type": "PERSON",
        "first_name": "Juan",
        "last_name": "Pérez García",
        "dni": "46781234",
        "phone": "987654321",
        "phone_whatsapp": "51987654321",
        "email": "juan.perez@example.com",
        "address": "Av. Aviación 123, Gamarra",
        "district": "La Victoria",
        "city": "Lima",
        "credit_limit": Decimal("1500.00"),
        "is_frequent": True,
        "notes": "Cliente frecuente - textiles",
    },
    {
        "type": "PERSON",
        "first_name": "María",
        "last_name": "Torres Díaz",
        "dni": "71234567",
        "phone": "976543210",
        "email": "maria.torres@example.com",
        "address": "Jr. Huánuco 456",
        "district": "Huánuco",
        "city": "Huánuco",
        "credit_limit": Decimal("800.00"),
        "is_frequent": False,
    },
    {
        "type": "PERSON",
        "first_name": "Carlos",
        "last_name": "Ramírez Soto",
        "dni": "42345678",
        "phone": "965432109",
        "phone_whatsapp": "51965432109",
        "email": "carlos.ramirez@example.com",
        "address": "Av. Perú 789",
        "district": "Trujillo",
        "city": "Trujillo",
        "credit_limit": Decimal("2000.00"),
        "is_frequent": True,
    },
    {
        "type": "PERSON",
        "first_name": "Lucía",
        "last_name": "Fernández Ríos",
        "dni": "73456789",
        "phone": "954321098",
        "email": "lucia.fernandez@example.com",
        "address": "Av. Grau 321",
        "district": "Piura",
        "city": "Piura",
        "credit_limit": Decimal("500.00"),
        "is_frequent": False,
    },
    {
        "type": "PERSON",
        "first_name": "Jorge",
        "last_name": "Vega Morales",
        "dni": "74567890",
        "phone": "943210987",
        "email": "jorge.vega@example.com",
        "address": "Jr. Lima 654",
        "district": "Cusco",
        "city": "Cusco",
        "credit_limit": Decimal("0.00"),
        "is_frequent": False,
        "is_blocked": True,
        "block_reason": "Mora pendiente - revisión créditos",
    },
    {
        "type": "COMPANY",
        "razon_social": "Textiles Andinos S.A.C.",
        "ruc": "20123456789",
        "phone": "01 712 3456",
        "phone_whatsapp": "51912345678",
        "email": "compras@textilesandinos.pe",
        "address": "Av. Industrial 987",
        "district": "Ate",
        "city": "Lima",
        "credit_limit": Decimal("15000.00"),
        "is_frequent": True,
        "notes": "Empresa mayorista",
    },
    {
        "type": "COMPANY",
        "razon_social": "Distribuidora Norte E.I.R.L.",
        "ruc": "20456789012",
        "phone": "044 234567",
        "email": "ventas@distribuidoranorte.pe",
        "address": "Av. España 432",
        "district": "Trujillo",
        "city": "Trujillo",
        "credit_limit": Decimal("8000.00"),
        "is_frequent": True,
    },
    {
        "type": "COMPANY",
        "razon_social": "Comercial Huánuco S.R.L.",
        "ruc": "20567890123",
        "phone": "062 512345",
        "email": "gerencia@comercialhuanuco.pe",
        "address": "Jr. 28 de Julio 111",
        "district": "Amarilis",
        "city": "Huánuco",
        "credit_limit": Decimal("5000.00"),
        "is_frequent": False,
    },
    {
        "type": "PERSON",
        "first_name": "Ana",
        "last_name": "Quispe Huamán",
        "dni": "75678901",
        "phone": "932109876",
        "email": "ana.quispe@example.com",
        "address": "Av. Universitaria 555",
        "district": "Comas",
        "city": "Lima",
        "credit_limit": Decimal("1200.00"),
        "is_frequent": True,
    },
    {
        "type": "PERSON",
        "first_name": "Pedro",
        "last_name": "Salazar León",
        "dni": "76789012",
        "phone": "921098765",
        "email": "pedro.salazar@example.com",
        "address": "Av. Central 777",
        "district": "Huancayo",
        "city": "Huancayo",
        "credit_limit": Decimal("300.00"),
        "is_frequent": False,
    },
]


async def seed_customers(db: AsyncSession) -> dict[str, int]:
    """Inserta 10 clientes ficticios de forma idempotente (por dni/ruc)."""
    existing_dnis = set(
        (await db.execute(select(Customer.dni).where(Customer.dni.is_not(None)))).scalars().all()
    )
    existing_rucs = set(
        (await db.execute(select(Customer.ruc).where(Customer.ruc.is_not(None)))).scalars().all()
    )
    created = 0
    for data in CUSTOMERS:
        dni = data.get("dni")
        ruc = data.get("ruc")
        if dni and dni in existing_dnis:
            continue
        if ruc and ruc in existing_rucs:
            continue
        customer = Customer(
            type=data.get("type", "PERSON"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            razon_social=data.get("razon_social"),
            dni=dni,
            ruc=ruc,
            phone=data.get("phone"),
            phone_whatsapp=data.get("phone_whatsapp"),
            email=data.get("email"),
            address=data.get("address"),
            district=data.get("district"),
            city=data.get("city"),
            credit_limit=data.get("credit_limit", Decimal("0")),
            is_blocked=data.get("is_blocked", False),
            block_reason=data.get("block_reason"),
            is_frequent=data.get("is_frequent", False),
            notes=data.get("notes"),
            active=True,
        )
        db.add(customer)
        created += 1
        if dni:
            existing_dnis.add(dni)
        if ruc:
            existing_rucs.add(ruc)

    if created:
        await db.commit()
    return {"customers_created": created, "customers_total": len(CUSTOMERS)}
