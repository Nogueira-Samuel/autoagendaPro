"""
Redis Cache Client

Async Redis client for caching with graceful degradation.

If Redis is not configured or unavailable, operations will fail silently
and log warnings instead of raising exceptions.
"""

import json
import logging
from typing import Any

import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client wrapper for caching.

    Implements singleton pattern to reuse connections.
    Gracefully handles missing Redis configuration.

    Usage:
        # Set value with TTL
        await RedisClient.set("user:123", {"name": "John"}, ttl=3600)

        # Get value
        data = await RedisClient.get("user:123")

        # Delete value
        await RedisClient.delete("user:123")

        # Check if exists
        exists = await RedisClient.exists("user:123")
    """

    _instance: redis.Redis | None = None
    _enabled: bool = True

    @classmethod
    async def get_client(cls) -> redis.Redis | None:
        """
        Get or create Redis client (singleton).

        Returns:
            Redis client instance or None if disabled

        Example:
            >>> client = await RedisClient.get_client()
            >>> if client:
            ...     await client.ping()
        """
        if not cls._enabled:
            return None

        if cls._instance is None:
            if not settings.REDIS_URL:
                logger.warning(
                    "Redis URL not configured. Caching will be disabled. "
                    "Set REDIS_URL environment variable to enable caching."
                )
                cls._enabled = False
                return None

            try:
                cls._instance = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )

                # Test connection
                await cls._instance.ping()

                logger.info(f"Redis client initialized: {settings.REDIS_URL}")

            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis: {e}. Caching will be disabled."
                )
                cls._enabled = False
                cls._instance = None
                return None

        return cls._instance

    @classmethod
    async def close(cls) -> None:
        """
        Close Redis connection.

        Should be called on application shutdown.

        Example:
            >>> await RedisClient.close()
        """
        if cls._instance:
            try:
                await cls._instance.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                cls._instance = None

    @classmethod
    async def set(
        cls,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Value is automatically JSON-serialized.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (None = no expiration)

        Returns:
            True if successful, False otherwise

        Example:
            >>> await RedisClient.set("user:123", {"name": "John"}, ttl=3600)
            True
        """
        client = await cls.get_client()
        if not client:
            return False

        try:
            # Serialize value to JSON
            serialized = json.dumps(value)

            # Set with or without TTL
            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)

            logger.debug(f"Cache SET: {key} (ttl={ttl})")
            return True

        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    @classmethod
    async def get(cls, key: str) -> Any | None:
        """
        Get value from cache.

        Automatically deserializes JSON.

        Args:
            key: Cache key

        Returns:
            Deserialized value or None if not found

        Example:
            >>> data = await RedisClient.get("user:123")
            >>> print(data)
            {'name': 'John'}
        """
        client = await cls.get_client()
        if not client:
            return None

        try:
            value = await client.get(key)

            if value is None:
                logger.debug(f"Cache MISS: {key}")
                return None

            # Deserialize JSON
            deserialized = json.loads(value)

            logger.debug(f"Cache HIT: {key}")
            return deserialized

        except json.JSONDecodeError as e:
            logger.error(f"Redis JSON decode error for key '{key}': {e}")
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    @classmethod
    async def delete(cls, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise

        Example:
            >>> await RedisClient.delete("user:123")
            True
        """
        client = await cls.get_client()
        if not client:
            return False

        try:
            result = await client.delete(key)
            logger.debug(f"Cache DELETE: {key} (deleted={result})")
            return bool(result)

        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False

    @classmethod
    async def exists(cls, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise

        Example:
            >>> exists = await RedisClient.exists("user:123")
            >>> print(exists)
            True
        """
        client = await cls.get_client()
        if not client:
            return False

        try:
            result = await client.exists(key)
            return bool(result)

        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False

    @classmethod
    async def expire(cls, key: str, ttl: int) -> bool:
        """
        Set expiration time for existing key.

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if expiration was set, False otherwise

        Example:
            >>> await RedisClient.expire("user:123", 3600)
            True
        """
        client = await cls.get_client()
        if not client:
            return False

        try:
            result = await client.expire(key, ttl)
            return bool(result)

        except Exception as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False

    @classmethod
    async def increment(cls, key: str, amount: int = 1) -> int | None:
        """
        Increment numeric value.

        Useful for counters, rate limiting, etc.

        Args:
            key: Cache key
            amount: Increment amount (default: 1)

        Returns:
            New value after increment or None on error

        Example:
            >>> count = await RedisClient.increment("api:requests:123")
            >>> print(count)
            1
        """
        client = await cls.get_client()
        if not client:
            return None

        try:
            result = await client.incrby(key, amount)
            logger.debug(f"Cache INCREMENT: {key} by {amount} = {result}")
            return result

        except Exception as e:
            logger.error(f"Redis INCREMENT error for key '{key}': {e}")
            return None

    @classmethod
    async def get_many(cls, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values at once.

        Args:
            keys: List of cache keys

        Returns:
            Dictionary mapping keys to values (missing keys are omitted)

        Example:
            >>> data = await RedisClient.get_many(["user:1", "user:2", "user:3"])
            >>> print(data)
            {'user:1': {...}, 'user:2': {...}}
        """
        client = await cls.get_client()
        if not client:
            return {}

        try:
            values = await client.mget(keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error for key '{key}'")

            logger.debug(f"Cache MGET: {len(keys)} keys, {len(result)} hits")
            return result

        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return {}

    @classmethod
    async def set_many(
        cls,
        mapping: dict[str, Any],
        ttl: int | None = None,
    ) -> bool:
        """
        Set multiple key-value pairs at once.

        Args:
            mapping: Dictionary of key-value pairs
            ttl: Optional TTL for all keys

        Returns:
            True if successful, False otherwise

        Example:
            >>> data = {"user:1": {...}, "user:2": {...}}
            >>> await RedisClient.set_many(data, ttl=3600)
            True
        """
        client = await cls.get_client()
        if not client:
            return False

        try:
            # Serialize all values
            serialized = {k: json.dumps(v) for k, v in mapping.items()}

            # Set all values
            await client.mset(serialized)

            # Set TTL if provided
            if ttl:
                pipeline = client.pipeline()
                for key in serialized.keys():
                    pipeline.expire(key, ttl)
                await pipeline.execute()

            logger.debug(f"Cache MSET: {len(mapping)} keys (ttl={ttl})")
            return True

        except Exception as e:
            logger.error(f"Redis MSET error: {e}")
            return False

    @classmethod
    async def clear_pattern(cls, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Use with caution in production!

        Args:
            pattern: Key pattern (supports wildcards *)

        Returns:
            Number of keys deleted

        Example:
            >>> deleted = await RedisClient.clear_pattern("user:*")
            >>> print(f"Deleted {deleted} keys")
        """
        client = await cls.get_client()
        if not client:
            return 0

        try:
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                deleted = await client.delete(*keys)
                logger.info(f"Cache CLEAR: pattern='{pattern}', deleted={deleted}")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"Redis CLEAR error for pattern '{pattern}': {e}")
            return 0
