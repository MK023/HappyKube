"""Rate limiting middleware using Redis."""

from functools import wraps
from typing import Any, Callable

from flask import g, jsonify, request

from ....config import get_logger
from ....infrastructure.cache import get_cache

logger = get_logger(__name__)


def rate_limit(max_requests: int = 100, window_seconds: int = 60) -> Callable:
    """
    Decorator for rate limiting endpoints.

    Uses Redis to track request counts per API key or IP.

    Args:
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Usage:
        @app.route("/expensive")
        @rate_limit(max_requests=10, window_seconds=60)
        def expensive_endpoint():
            return {"data": "..."}
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache()

            # Identify requester (API key or IP)
            if hasattr(g, "api_key"):
                identifier = f"api_key:{g.api_key}"
            else:
                identifier = f"ip:{request.remote_addr}"

            # Rate limit key
            rate_key = f"rate_limit:{identifier}:{request.endpoint}"

            # Increment counter
            current_count = cache.increment(rate_key, amount=1, ttl=window_seconds)

            if current_count is None:
                # Redis error - allow request but log warning
                logger.warning("Rate limit Redis error, allowing request")
                return f(*args, **kwargs)

            # Check if limit exceeded
            if current_count > max_requests:
                logger.warning(
                    "Rate limit exceeded",
                    identifier=identifier,
                    count=current_count,
                    limit=max_requests,
                )
                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "limit": max_requests,
                            "window": window_seconds,
                            "retry_after": cache.get_ttl(rate_key) or window_seconds,
                        }
                    ),
                    429,
                )

            # Add rate limit headers
            response = f(*args, **kwargs)

            # If response is tuple (body, status_code), extract body
            if isinstance(response, tuple):
                response_body, status_code = response[0], response[1]
            else:
                response_body = response
                status_code = 200

            # Add headers if response is Flask response object
            if hasattr(response_body, "headers"):
                response_body.headers["X-RateLimit-Limit"] = str(max_requests)
                response_body.headers["X-RateLimit-Remaining"] = str(
                    max(0, max_requests - current_count)
                )
                response_body.headers["X-RateLimit-Reset"] = str(
                    cache.get_ttl(rate_key) or window_seconds
                )

            return response_body, status_code if isinstance(response, tuple) else response_body

        return decorated_function

    return decorator
