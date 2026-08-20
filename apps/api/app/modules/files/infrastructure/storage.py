"""Proveedor de almacenamiento S3 compatible con MinIO (boto3)."""

from __future__ import annotations

import io
from functools import lru_cache

import boto3
from app.core.config import settings
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError


class StorageError(Exception):
    """Error genérico de almacenamiento."""


class StorageProvider:
    """Wrapper sobre boto3 para operaciones S3 (MinIO)."""

    def __init__(self, endpoint: str, access_key: str, secret_key: str, bucket: str) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4", retries={"max_attempts": 2}),
        )

    async def upload_bytes(self, key: str, data: bytes, mime_type: str) -> None:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=io.BytesIO(data),
                ContentType=mime_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Fallo al subir objeto: {exc}") from exc

    async def get_bytes(self, key: str) -> bytes:
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Fallo al leer objeto: {exc}") from exc

    async def delete(self, key: str) -> None:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError(f"Fallo al eliminar objeto: {exc}") from exc


@lru_cache
def get_storage() -> StorageProvider:
    """Singleton del storage provider."""
    return StorageProvider(
        endpoint=settings.S3_ENDPOINT,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket=settings.S3_BUCKET_NAME,
    )


async def upload_bytes(key: str, data: bytes, mime_type: str) -> None:
    await get_storage().upload_bytes(key, data, mime_type)


async def get_bytes(key: str) -> bytes:
    return await get_storage().get_bytes(key)


async def delete_object(key: str) -> None:
    await get_storage().delete(key)
