"""FastAPI application factory."""

import gc
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import get_logger, get_settings, init_sentry, setup_logging

logger = get_logger(__name__)
settings = get_settings()

# Global cache for analyzers
_analyzer_cache = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for resource optimization (512MB free tier).

    Handles:
    - Lazy loading of ML models
    - Memory cleanup on shutdown
    - Connection pool management
    """
    # Startup
    logger.info(
        "Application starting",
        env=settings.app_env,
        version=settings.app_version,
    )

    # Pre-warm critical connections (lazy load models)
    logger.info("Resources initialized (models will load on-demand)")

    yield

    # Shutdown - cleanup resources
    logger.info("Application shutting down, cleaning up resources")

    # Close Groq analyzer HTTP client
    try:
        from infrastructure.ml.model_factory import get_model_factory

        factory = get_model_factory()
        await factory.cleanup()
        logger.info("Groq analyzer closed")
    except Exception as e:
        logger.error("Error closing Groq analyzer", error=str(e))

    # Close Redis connection (sync operation)
    try:
        from infrastructure.cache import get_cache

        cache = get_cache()
        cache.close()
    except Exception as e:
        logger.error("Error closing Redis", error=str(e))

    # Close database connections
    try:
        from infrastructure.database import close_database

        close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database", error=str(e))

    # Clear analyzer cache
    _analyzer_cache.clear()

    # Force garbage collection
    gc.collect()

    logger.info("Cleanup completed")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI app
    """
    # Initialize Axiom for centralized logging (production only)
    # TEMPORARILY DISABLED: Waiting for axiom-py SDK to support EU edge deployments (Q1 2026)
    # init_axiom()

    # Setup logging with service identifier (Axiom disabled until SDK supports edge deployments)
    setup_logging(service_name="api", axiom_enabled=False)

    # Log Axiom configuration status
    if settings.axiom_api_token and not settings.is_development:
        logger.info(
            "Axiom logging enabled",
            dataset=settings.axiom_dataset,
            org_id=settings.axiom_org_id,
            url=settings.axiom_url,
        )

    # Initialize Sentry for error tracking (production only)
    init_sentry()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Emotion analysis API using Groq (Llama 3.3 70B)",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Configure CORS
    if settings.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-API-Key", "Authorization"],
        )
        logger.info("CORS enabled", origins=settings.cors_origins)

    # Configure rate limiting
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add security middlewares (CRITICAL - must be first)
    from .middleware.security import (
        APIKeyMiddleware,
        RequestSizeLimitMiddleware,
        SecurityHeadersMiddleware,
    )

    # Request size limit (first line of defense)
    app.add_middleware(RequestSizeLimitMiddleware)
    logger.info("Request size limit enabled", max_size="1MB")

    # API Key authentication (blocks unauthorized access)
    app.add_middleware(APIKeyMiddleware)
    logger.info("API Key authentication enabled")

    # Security headers (add to all responses)
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers enabled")

    # Add audit middleware (if enabled)
    if settings.is_production:
        from .middleware.audit import AuditMiddleware

        app.add_middleware(AuditMiddleware)
        logger.info("Audit logging enabled")

    # Include routers (lazy import to avoid circular dependencies)
    from .routes import emotion, health, reports, telegram_webhook

    app.include_router(health.router)
    app.include_router(emotion.router)
    app.include_router(reports.router)
    logger.info("Monthly reports API enabled", endpoint="/reports")

    # Telegram Webhook (HappyKube 3.0)
    app.include_router(telegram_webhook.router)
    logger.info("Telegram webhook enabled", endpoint="/telegram/webhook")

    # Add Prometheus metrics endpoint (if enabled)
    if settings.prometheus_enabled:
        from .routes import metrics

        app.include_router(metrics.router)
        logger.info("Prometheus metrics enabled", endpoint="/metrics")

    logger.info(
        "FastAPI app created with lifespan management",
        env=settings.app_env,
        debug=settings.debug,
        version=settings.app_version,
    )

    return app


# Create app instance
app = create_app()
