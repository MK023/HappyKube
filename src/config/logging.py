"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from .settings import get_settings


def setup_logging(service_name: str | None = None, axiom_enabled: bool = False) -> None:
    """Configure structured logging with structlog.

    Args:
        service_name: Optional service identifier (e.g., 'bot', 'api') to distinguish logs
        axiom_enabled: Enable sending logs to Axiom (production only)
    """
    settings = get_settings()

    # Define log processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.is_development:
        # Pretty console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]

    # Add Axiom processor if enabled (production only)
    if axiom_enabled and not settings.is_development:
        try:
            from .axiom import get_axiom_processor

            # Insert before JSON renderer to capture structured data
            processors.insert(-1, get_axiom_processor())
            logger = structlog.get_logger(__name__)
            logger.info("Axiom logging processor enabled")
        except Exception as e:
            # Log error but don't crash - graceful degradation
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to enable Axiom processor (non-fatal): {e}"
            )

    # Configure structlog
    structlog.configure(
        processors=processors,  # type: ignore
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Set log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.db_echo else logging.WARNING
    )

    # Bind service name to all logs if provided
    if service_name:
        structlog.contextvars.bind_contextvars(service=service_name)


def get_logger(name: str) -> Any:
    """Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)
