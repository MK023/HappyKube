"""Security middleware for API protection."""

import secrets
from typing import Optional

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from config import get_logger, settings

logger = get_logger(__name__)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key authentication middleware.

    Protects ALL endpoints except health checks and metrics.
    Requires X-API-Key header with valid key.
    """

    # Endpoints that don't require authentication
    PUBLIC_PATHS = {"/", "/healthz", "/ping", "/readyz", "/metrics", "/docs", "/redoc", "/openapi.json"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Verify API key before processing request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response or 403 Forbidden
        """
        # Skip auth for public endpoints
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # Extract API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning(
                "Unauthorized request - missing API key",
                path=request.url.path,
                ip=request.client.host if request.client else None
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Missing API key. Include X-API-Key header.",
                    "error": "unauthorized"
                }
            )

        # Validate API key (constant-time comparison to prevent timing attacks)
        if not settings.api_keys or not self._validate_key(api_key, settings.api_keys):
            logger.warning(
                "Unauthorized request - invalid API key",
                path=request.url.path,
                ip=request.client.host if request.client else None,
                key_prefix=api_key[:8] if len(api_key) >= 8 else "***"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Invalid API key",
                    "error": "unauthorized"
                }
            )

        # Valid key - proceed
        return await call_next(request)

    @staticmethod
    def _validate_key(provided_key: str, valid_keys: list[str]) -> bool:
        """
        Validate API key using constant-time comparison.

        Args:
            provided_key: Key from request
            valid_keys: List of valid keys

        Returns:
            True if valid, False otherwise
        """
        return any(secrets.compare_digest(provided_key, valid_key) for valid_key in valid_keys)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware.

    Adds security headers to all responses.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Add security headers to response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response with security headers
        """
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (strict)
        if settings.is_production:
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )

        # Remove server header (if present)
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Request size limit middleware.

    Protects against large payload attacks.
    """

    MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Check request size before processing.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response or 413 Payload Too Large
        """
        # Check Content-Length header
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.MAX_REQUEST_SIZE:
                logger.warning(
                    "Request too large",
                    size=content_length,
                    max_size=self.MAX_REQUEST_SIZE,
                    path=request.url.path,
                    ip=request.client.host if request.client else None
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={
                        "detail": f"Request size {content_length} bytes exceeds limit of {self.MAX_REQUEST_SIZE} bytes",
                        "error": "payload_too_large"
                    }
                )

        return await call_next(request)
