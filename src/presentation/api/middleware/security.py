"""Security middleware for API protection."""

from uuid import UUID

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from config import get_logger, get_settings
from infrastructure.database import get_engine
from infrastructure.repositories import APIKeyRepository

logger = get_logger(__name__)
settings = get_settings()


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    API Key authentication middleware with database backend.

    Protects ALL endpoints except health checks and metrics.
    Requires X-API-Key header with valid key stored in database.

    Security features:
    - Bcrypt-hashed keys (no plaintext storage)
    - Expiration checking
    - Rate limit per key
    - Last used timestamp tracking
    """

    # Endpoints that don't require authentication
    PUBLIC_PATHS = {"/", "/healthz", "/ping", "/readyz", "/metrics", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app):
        """Initialize middleware with database connection."""
        super().__init__(app)
        self._engine = None
        self._api_key_repo = None

    def _get_repository(self) -> APIKeyRepository:
        """Lazy-load API key repository."""
        if self._api_key_repo is None:
            self._engine = get_engine()
            self._api_key_repo = APIKeyRepository(self._engine)
        return self._api_key_repo

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

        # Validate API key against database (with bcrypt verification)
        try:
            repo = self._get_repository()
            is_valid, api_key_id, rate_limit = repo.validate_key(api_key)

            if not is_valid:
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

            # Store API key ID in request state for audit logging
            request.state.api_key_id = api_key_id
            request.state.rate_limit = rate_limit

        except Exception as e:
            logger.error(
                "Error validating API key",
                path=request.url.path,
                error=str(e),
                exc_info=e
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Authentication service error",
                    "error": "internal_error"
                }
            )

        # Valid key - proceed
        return await call_next(request)


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
