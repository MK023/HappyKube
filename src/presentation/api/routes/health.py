"""Health check routes."""

from fastapi import APIRouter, Response, status

from config import get_logger, get_settings
from infrastructure.cache import get_cache
from infrastructure.database import health_check as db_health_check

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["health"])


@router.get(
    "/",
    summary="API Information",
    description="Get basic API metadata including version, environment, and available endpoints.",
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "service": "HappyKube API",
                        "version": "2.0.0",
                        "status": "running",
                        "environment": "production",
                        "endpoints": {
                            "health": "/healthz",
                            "ping": "/ping",
                            "readiness": "/readyz",
                        },
                    }
                }
            },
        }
    },
)
async def root():
    """
    Root endpoint.

    Returns basic API information.
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.app_env,
        "endpoints": {
            "health": "/healthz",
            "ping": "/ping",
            "readiness": "/readyz",
            "docs": "/docs" if settings.debug else None,
        },
    }


@router.get(
    "/healthz",
    summary="Liveness probe",
    description="Kubernetes liveness probe. Returns 200 if service process is running.",
    responses={
        200: {
            "description": "Service is alive",
            "content": {
                "application/json": {"example": {"status": "healthy", "service": "HappyKube API"}}
            },
        }
    },
)
async def healthz():
    """
    Basic health check (liveness probe).

    Returns 200 if service is running.
    """
    return {"status": "healthy", "service": settings.app_name}


@router.get("/healthz/db")
async def healthz_db(response: Response):
    """Database health check."""
    try:
        if db_health_check():
            return {"status": "healthy", "service": "database"}
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unhealthy", "service": "database"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "service": "database", "error": str(e)}


@router.get("/healthz/redis")
async def healthz_redis(response: Response):
    """Redis health check."""
    try:
        cache = get_cache()
        if cache.health_check():
            return {"status": "healthy", "service": "redis"}
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unhealthy", "service": "redis"}
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "service": "redis", "error": str(e)}


@router.get("/ping")
@router.head("/ping")
async def ping(response: Response):
    """
    Lightweight ping endpoint for Fly.io health checks.

    Supports both GET and HEAD methods.
    Returns 200 if the service is running (minimal resource usage).
    For comprehensive health checks, use /readyz instead.
    """
    # Lightweight response - just confirms service is alive
    # No DB/Redis checks to reduce resource consumption from frequent health checks
    return "pong"


@router.get(
    "/readyz",
    summary="Readiness probe",
    description="""
    Kubernetes readiness probe. Checks if service is ready to accept traffic.

    **Checks:**
    - PostgreSQL database connectivity
    - Redis cache connectivity
    - Groq API availability

    Returns 200 if all dependencies are healthy, 503 otherwise.
    """,
    responses={
        200: {
            "description": "Service is ready",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ready",
                        "checks": {
                            "database": "healthy",
                            "redis": "healthy",
                            "groq_api": "healthy",
                        },
                    }
                }
            },
        },
        503: {
            "description": "Service not ready",
            "content": {
                "application/json": {
                    "example": {
                        "status": "not ready",
                        "checks": {
                            "database": "healthy",
                            "redis": "unhealthy",
                            "groq_api": "healthy",
                        },
                    }
                }
            },
        },
    },
)
async def readyz(response: Response):
    """
    Readiness check (readiness probe).

    Checks database, Redis, and Groq API connectivity.
    """
    try:
        # Check database
        db_healthy = db_health_check()

        # Check Redis
        cache = get_cache()
        redis_healthy = cache.health_check()

        # Check Groq API via existing analyzer client (reuses connection pool)
        groq_healthy = False
        try:
            from infrastructure.ml.model_factory import get_model_factory

            factory = get_model_factory()
            analyzer = factory.get_groq_analyzer()
            groq_response = await analyzer._client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            )
            groq_healthy = groq_response.status_code == 200
        except Exception as e:
            logger.warning("Groq API health check failed", error=str(e))
            groq_healthy = False

        all_healthy = db_healthy and redis_healthy and groq_healthy

        if all_healthy:
            return {
                "status": "ready",
                "checks": {
                    "database": "healthy",
                    "redis": "healthy",
                    "groq_api": "healthy",
                },
            }
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "not ready",
                "checks": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "redis": "healthy" if redis_healthy else "unhealthy",
                    "groq_api": "healthy" if groq_healthy else "unhealthy",
                },
            }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "error": str(e)}
