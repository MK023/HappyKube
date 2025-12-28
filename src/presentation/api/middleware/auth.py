"""API authentication middleware."""

from functools import wraps
from typing import Any, Callable

from flask import Request, g, jsonify, request

from ....config import get_logger, settings

logger = get_logger(__name__)


def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require valid API key for endpoint.

    Checks X-API-Key header against configured API keys.

    Usage:
        @app.route("/protected")
        @require_api_key
        def protected_endpoint():
            return {"data": "secret"}
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning("Missing API key in request", path=request.path, ip=request.remote_addr)
            return jsonify({"error": "Missing API key"}), 401

        # Validate API key
        if api_key not in settings.api_keys:
            logger.warning(
                "Invalid API key",
                path=request.path,
                ip=request.remote_addr,
                key_prefix=api_key[:8] if api_key else "None",
            )
            return jsonify({"error": "Invalid API key"}), 401

        # Store API key in request context for rate limiting
        g.api_key = api_key

        logger.debug("API key validated", path=request.path)

        return f(*args, **kwargs)

    return decorated_function


def optional_api_key(f: Callable) -> Callable:
    """
    Decorator for optional API key authentication.

    Validates if present, but doesn't reject if missing.
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        api_key = request.headers.get("X-API-Key")

        if api_key and api_key in settings.api_keys:
            g.api_key = api_key
            g.authenticated = True
        else:
            g.authenticated = False

        return f(*args, **kwargs)

    return decorated_function
