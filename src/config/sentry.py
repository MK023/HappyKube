"""Sentry integration for error tracking."""

from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .logging import get_logger
from .settings import get_settings

logger = get_logger(__name__)


def init_sentry() -> None:
    """
    Initialize Sentry SDK for error tracking.

    Only initializes if:
    - Running in production environment
    - SENTRY_DSN is configured
    """
    settings = get_settings()

    if not settings.sentry_dsn:
        logger.info("Sentry not configured (SENTRY_DSN missing)")
        return

    if not settings.is_production:
        logger.info("Sentry disabled in non-production environment", env=settings.app_env)
        return

    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            release=f"{settings.app_name}@{settings.app_version}",

            # Performance monitoring
            traces_sample_rate=settings.sentry_traces_sample_rate,

            # Integrations
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],

            # Additional options
            send_default_pii=False,  # Don't send PII by default (GDPR compliance)
            attach_stacktrace=True,
            max_breadcrumbs=50,

            # Filter events
            before_send=_before_send,
        )

        logger.info(
            "Sentry initialized",
            dsn_prefix=settings.sentry_dsn[:20] + "...",
            environment=settings.app_env,
            release=f"{settings.app_name}@{settings.app_version}",
            traces_sample_rate=settings.sentry_traces_sample_rate,
        )

    except Exception as e:
        logger.error("Failed to initialize Sentry", error=str(e))


def _before_send(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """
    Filter/modify events before sending to Sentry.

    Args:
        event: Sentry event dict
        hint: Additional context

    Returns:
        Modified event or None to skip
    """
    # Skip health check errors (not actionable)
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if "health" in str(exc_value).lower():
            return None

    # Scrub sensitive data from request body
    if "request" in event and "data" in event["request"]:
        # Remove potential API keys, tokens from logged data
        data = event["request"]["data"]
        if isinstance(data, dict):
            for sensitive_key in ["api_key", "token", "password", "secret"]:
                if sensitive_key in data:
                    data[sensitive_key] = "[REDACTED]"

    return event
