"""Seeds de cajas - F04-14: CashRegister general y de ventas."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.cash.domain.models import CashRegister
from app.modules.users.domain.models import User

# (nombre, email propietario, is_general)
CASH_REGISTERS: list[tuple[str, str, bool]] = [
    ("Caja General", "owner@hasbun.dev", True),
    ("Caja Ventas", "ventas@hasbun.dev", False),
]


async def seed_cash_registers(db: AsyncSession) -> dict[str, int]:
    """Crea 2 CashRegister idempotentes buscando por name.

    - Caja General -> owner@hasbun.dev, is_general=True
    - Caja Ventas  -> ventas@hasbun.dev, is_general=False
    """
    # Resolver usuarios
    users = {
        u.email: u
        for u in (await db.execute(select(User).where(User.email.in_([e for _, e, _ in CASH_REGISTERS])))).scalars().all()
    }

    existing_names = set((await db.execute(select(CashRegister.name))).scalars().all())
    created = 0

    for name, email, is_general in CASH_REGISTERS:
        if name in existing_names:
            continue
        user = users.get(email)
        register = CashRegister(
            name=name,
            user_id=user.id if user else None,
            is_general=is_general,
            active=True,
        )
        db.add(register)
        created += 1
        existing_names.add(name)

    if created:
        await db.commit()
    return {"cash_registers_created": created, "cash_registers_total": len(CASH_REGISTERS)}


# Alias requerido por __init__.py (seed_cash)
seed_cash = seed_cash_registers
