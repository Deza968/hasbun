"""Almacenamiento en MinIO/S3 usando boto3 (#F02-10)."""

from __future__ import annotations

import logging

import boto3
from app.core.config import settings
from app.modules.files.domain.storage import StorageProvider
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("hasbun.files")


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


class MinIOStorageProvider(StorageProvider):
    def __init__(self, bucket: str | None = None) -> None:
        self.bucket = bucket or settings.S3_BUCKET_NAME

    async def upload(self, *, storage_key: str, data: bytes, mime_type: str) -> None:
        client = _client()
        try:
            client.put_object(
                Bucket=self.bucket,
                Key=storage_key,
                Body=data,
                ContentType=mime_type,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Fallo upload a MinIO (%s)", storage_key)
            raise RuntimeError(f"Fallo al subir archivo: {exc}") from exc

    async def get_url(self, storage_key: str, *, ttl_seconds: int) -> str:
        client = _client()
        try:
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": storage_key},
                ExpiresIn=ttl_seconds,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Fallo generar URL firmada (%s)", storage_key)
            raise RuntimeError(f"Fallo al generar URL: {exc}") from exc

    async def delete(self, storage_key: str) -> None:
        client = _client()
        try:
            client.delete_object(Bucket=self.bucket, Key=storage_key)
        except (BotoCoreError, ClientError) as exc:
            logger.exception("Fallo delete en MinIO (%s)", storage_key)
            raise RuntimeError(f"Fallo al eliminar archivo: {exc}") from exc


def build_storage() -> StorageProvider:
    return MinIOStorageProvider()
