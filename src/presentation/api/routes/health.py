"""Health check routes."""

from fastapi import APIRouter, Response, status

from config import get_logger, settings
from infrastructure.cache import get_cache
from infrastructure.database import health_check as db_health_check

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
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
        }
    }


@router.get("/healthz")
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


@router.get("/healthz/huggingface")
async def healthz_huggingface(response: Response):
    """HuggingFace API health check."""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            hf_response = await client.get(
                "https://api-inference.huggingface.co/status",
                headers={"Authorization": f"Bearer {settings.huggingface_token}"}
            )
            if hf_response.status_code == 200:
                return {"status": "healthy", "service": "huggingface_api"}
            else:
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                return {"status": "unhealthy", "service": "huggingface_api"}
    except Exception as e:
        logger.error("HuggingFace API health check failed", error=str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "service": "huggingface_api", "error": str(e)}


@router.get("/ping")
async def ping(response: Response):
    """
    Ping endpoint for UptimeRobot with DB and Redis check.

    Returns 200 if DB and Redis are healthy.
    """
    try:
        # Quick health check
        db_ok = db_health_check()
        cache = get_cache()
        redis_ok = cache.health_check()

        if db_ok and redis_ok:
            return "pong"
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return "unhealthy"

    except Exception as e:
        logger.error("Ping check failed", error=str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return "error"


@router.get("/readyz")
async def readyz(response: Response):
    """
    Readiness check (readiness probe).

    Checks database, Redis, and HuggingFace API connectivity.
    """
    import httpx

    try:
        # Check database
        db_healthy = db_health_check()

        # Check Redis
        cache = get_cache()
        redis_healthy = cache.health_check()

        # Check HuggingFace API
        hf_healthy = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                hf_response = await client.get(
                    "https://api-inference.huggingface.co/status",
                    headers={"Authorization": f"Bearer {settings.huggingface_token}"}
                )
                hf_healthy = hf_response.status_code == 200
        except Exception as e:
            logger.warning("HuggingFace API health check failed", error=str(e))
            hf_healthy = False

        all_healthy = db_healthy and redis_healthy and hf_healthy

        if all_healthy:
            return {
                "status": "ready",
                "checks": {
                    "database": "healthy",
                    "redis": "healthy",
                    "huggingface_api": "healthy",
                },
            }
        else:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {
                "status": "not ready",
                "checks": {
                    "database": "healthy" if db_healthy else "unhealthy",
                    "redis": "healthy" if redis_healthy else "unhealthy",
                    "huggingface_api": "healthy" if hf_healthy else "unhealthy",
                },
            }

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "error": str(e)}
