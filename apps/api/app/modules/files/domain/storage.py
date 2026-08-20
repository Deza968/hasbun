"""Abstracción de almacenamiento de archivos (#F02-10)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    bucket: str

    @abstractmethod
    async def upload(self, *, storage_key: str, data: bytes, mime_type: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_url(self, storage_key: str, *, ttl_seconds: int) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, storage_key: str) -> None:
        raise NotImplementedError
