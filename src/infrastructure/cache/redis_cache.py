"""Redis cache implementation for performance optimization."""

import json
from typing import Any

import redis
from redis import Redis
from redis.exceptions import RedisError

from config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class RedisCache:
    """
    Redis cache wrapper for caching ML predictions and rate limiting.

    Features:
    - Automatic JSON serialization/deserialization
    - TTL support
    - Connection pooling
    - Error handling with graceful degradation
    """

    def __init__(self, redis_client: Redis | None = None) -> None:
        """
        Initialize Redis cache.

        Args:
            redis_client: Optional Redis client (for testing/DI)
        """
        if redis_client is not None:
            self._client = redis_client
        else:
            # Create Redis client with connection pooling and retry logic
            self._client = redis.from_url(
                settings.get_redis_url(),
                decode_responses=False,  # We handle encoding/decoding ourselves
                socket_connect_timeout=10,  # 5 → 10s for Render free tier
                socket_timeout=10,  # 5 → 10s
                retry_on_timeout=True,
                retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError],
                max_connections=10,  # Connection pooling
                health_check_interval=30,  # Check connections every 30s
            )

        logger.info("Redis cache initialized with connection pool", url=settings.get_redis_url())

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value (deserialized from JSON) or None if not found/error
        """
        try:
            value = self._client.get(key)
            if value is None:
                logger.debug("Cache miss", key=key)
                return None

            # Deserialize JSON
            deserialized = json.loads(value)
            logger.debug("Cache hit", key=key)
            return deserialized

        except RedisError as e:
            logger.error("Redis get error (degrading gracefully)", key=key, error=str(e))
            return None
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in cache", key=key, error=str(e))
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """
        Set value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (defaults to settings.redis_cache_ttl)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize to JSON
            serialized = json.dumps(value)

            # Use default TTL if not specified
            ttl_seconds = ttl if ttl is not None else settings.redis_cache_ttl

            # Set with expiration
            self._client.setex(key, ttl_seconds, serialized)
            logger.debug("Cache set", key=key, ttl=ttl_seconds)
            return True

        except (RedisError, TypeError, json.JSONEncodeError) as e:
            logger.error("Redis set error", key=key, error=str(e))
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key was deleted, False otherwise
        """
        try:
            deleted = self._client.delete(key)
            logger.debug("Cache delete", key=key, deleted=bool(deleted))
            return bool(deleted)

        except RedisError as e:
            logger.error("Redis delete error", key=key, error=str(e))
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self._client.exists(key))
        except RedisError as e:
            logger.error("Redis exists error", key=key, error=str(e))
            return False

    def increment(self, key: str, amount: int = 1, ttl: int | None = None) -> int | None:
        """
        Increment counter (for rate limiting).

        Args:
            key: Counter key
            amount: Amount to increment
            ttl: Set TTL if key doesn't exist

        Returns:
            New counter value or None on error
        """
        try:
            # Increment counter
            new_value = self._client.incrby(key, amount)

            # Set TTL if this is a new key
            if ttl is not None and new_value == amount:
                self._client.expire(key, ttl)

            return int(new_value)

        except RedisError as e:
            logger.error("Redis increment error", key=key, error=str(e))
            return None

    def get_ttl(self, key: str) -> int | None:
        """
        Get remaining TTL for key.

        Args:
            key: Cache key

        Returns:
            TTL in seconds, -1 if no expiry, None if key doesn't exist
        """
        try:
            ttl = self._client.ttl(key)
            return int(ttl) if ttl >= -1 else None
        except RedisError as e:
            logger.error("Redis TTL error", key=key, error=str(e))
            return None

    def flush_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "user:123:*")

        Returns:
            Number of keys deleted
        """
        try:
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                logger.info("Flushed cache pattern", pattern=pattern, deleted=deleted)
                return int(deleted)
            return 0

        except RedisError as e:
            logger.error("Redis flush pattern error", pattern=pattern, error=str(e))
            return 0

    def health_check(self) -> bool:
        """
        Check if Redis is reachable.

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            return self._client.ping()
        except RedisError as e:
            logger.error("Redis health check failed", error=str(e))
            return False

    def close(self) -> None:
        """Close Redis connection."""
        try:
            self._client.close()
            logger.info("Redis connection closed")
        except RedisError as e:
            logger.error("Error closing Redis connection", error=str(e))


# Singleton instance
_cache_instance: RedisCache | None = None


def get_cache() -> RedisCache:
    """
    Get singleton Redis cache instance.

    Returns:
        RedisCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance
