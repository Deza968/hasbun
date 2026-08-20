"""Repository de FileObject."""

from __future__ import annotations

import uuid

from app.modules.files.domain.models import FileObject
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession


async def get_by_id(db: AsyncSession, file_id: uuid.UUID) -> FileObject | None:
    return await db.get(FileObject, file_id)


async def create(db: AsyncSession, file: FileObject) -> FileObject:
    db.add(file)
    await db.commit()
    await db.refresh(file)
    return file


async def mark_deleted(db: AsyncSession, file_id: uuid.UUID) -> None:
    await db.execute(
        update(FileObject).where(FileObject.id == file_id).values(is_deleted=True)
    )
    await db.commit()


async def list_by_uploader(db: AsyncSession, user_id: uuid.UUID) -> list[FileObject]:
    return list(
        (
            await db.execute(
                select(FileObject)
                .where(FileObject.uploaded_by == user_id)
                .order_by(FileObject.created_at.desc())
            )
        ).scalars().all()
    )
