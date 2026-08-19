"""Cliente Redis (asyncio) y helpers de sesiones/blocklist.

Todas las funciones toleran fallos de Redis: si Redis cae, la aplicación
continúa (los tokens JWT siguen siendo válidos por su firma y expiración).
"""

from __future__ import annotations

import logging
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger("hasbun.redis")

redis_client = aioredis.from_url(
    settings.REDIS_URL, encoding="utf-8", decode_responses=True
)

SESSION_TTL_SECONDS = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
LOGIN_FAIL_TTL_SECONDS = 15 * 60
LOGIN_FAIL_MAX = 10


def _session_key(user_id: str, jti: str) -> str:
    return f"session:{user_id}:{jti}"


async def store_refresh_session(user_id: str, jti: str) -> None:
    """Guarda una sesión de refresh activa con TTL."""
    try:
        await redis_client.set(_session_key(user_id, jti), "1", ex=SESSION_TTL_SECONDS)
    except Exception:  # noqa: BLE001
        logger.exception("Redis store_refresh_session falló")


async def refresh_session_exists(user_id: str, jti: str) -> bool:
    try:
        return bool(await redis_client.get(_session_key(user_id, jti)))
    except Exception:  # noqa: BLE001
        logger.exception("Redis refresh_session_exists falló")
        return False


async def revoke_session(user_id: str, jti: str) -> None:
    try:
        await redis_client.delete(_session_key(user_id, jti))
    except Exception:  # noqa: BLE001
        logger.exception("Redis revoke_session falló")


async def revoke_all_sessions(user_id: str) -> None:
    """Invalida todas las sesiones activas de un usuario."""
    try:
        keys = await redis_client.keys(f"session:{user_id}:*")
        if keys:
            await redis_client.delete(*keys)
    except Exception:  # noqa: BLE001
        logger.exception("Redis revoke_all_sessions falló")


async def blocklist_access_token(jti: str, ttl: int) -> None:
    """Agrega un access token a la blocklist (logout)."""
    try:
        await redis_client.set(f"blocklist:{jti}", "1", ex=ttl)
    except Exception:  # noqa: BLE001
        logger.exception("Redis blocklist falló")


async def is_access_token_blocked(jti: str) -> bool:
    try:
        return bool(await redis_client.get(f"blocklist:{jti}"))
    except Exception:  # noqa: BLE001
        logger.exception("Redis is_blocked falló")
        return False


async def register_login_failure(ip: str) -> bool:
    """Registra un intento fallido. Retorna True si quedó bloqueado."""
    try:
        key = f"login_fail:{ip}"
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, LOGIN_FAIL_TTL_SECONDS)
        return count >= LOGIN_FAIL_MAX
    except Exception:  # noqa: BLE001
        logger.exception("Redis register_login_failure falló")
        return False


async def reset_login_failures(ip: str) -> None:
    try:
        await redis_client.delete(f"login_fail:{ip}")
    except Exception:  # noqa: BLE001
        logger.exception("Redis reset_login_failures falló")


async def set_permission_cache(user_id: str, codenames: list[str], ttl: int = 300) -> None:
    """Cachea los permisos del usuario en Redis (TTL 5 min)."""
    try:
        key = f"perms:{user_id}"
        await redis_client.delete(key)
        if codenames:
            await redis_client.rpush(key, *codenames)
            await redis_client.expire(key, ttl)
    except Exception:  # noqa: BLE001
        logger.exception("Redis set_permission_cache falló")


async def get_permission_cache(user_id: str) -> list[str] | None:
    try:
        values: list[Any] = await redis_client.lrange(f"perms:{user_id}", 0, -1)
        return [str(v) for v in values] if values else None
    except Exception:  # noqa: BLE001
        logger.exception("Redis get_permission_cache falló")
        return None


async def invalidate_permission_cache(user_id: str) -> None:
    try:
        await redis_client.delete(f"perms:{user_id}")
    except Exception:  # noqa: BLE001
        logger.exception("Redis invalidate_permission_cache falló")
