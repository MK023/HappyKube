"""Audit logging middleware."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from config import get_logger
from infrastructure.database import get_db_session
from infrastructure.database.models import AuditLogModel

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging.

    Logs all API requests for security and compliance.
    """

    EXCLUDED_PATHS = {"/healthz", "/ping", "/readyz", "/metrics", "/"}

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """
        Process request and log to audit table.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Skip audit logging for health checks
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Extract request details
        user_id = None  # TODO: Extract from JWT token if authenticated
        action = f"{request.method} {request.url.path}"
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Process request
        response = await call_next(request)

        # Log to database (don't block response)
        try:
            # Use context manager properly
            with get_db_session() as db:
                audit_entry = AuditLogModel(
                    id=uuid4(),
                    user_id=user_id,
                    action=action,
                    endpoint=request.url.path,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(audit_entry)
                db.commit()
                logger.debug("Audit log created", action=action, ip=ip_address)
        except Exception as e:
            logger.error("Failed to create audit log", error=str(e), action=action)
            # Don't fail the request if audit logging fails

        return response
