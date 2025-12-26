"""Health check routes."""

from flask import Blueprint, jsonify

from ....config import get_logger, settings
from ....infrastructure.cache import get_cache
from ....infrastructure.database import health_check as db_health_check

logger = get_logger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/healthz", methods=["GET"])
def healthz():
    """
    Basic health check (liveness probe).

    Returns 200 if service is running.
    """
    return jsonify({"status": "healthy", "service": settings.app_name}), 200


@health_bp.route("/readyz", methods=["GET"])
def readyz():
    """
    Readiness check (readiness probe).

    Checks database and Redis connectivity.
    """
    try:
        # Check database
        db_healthy = db_health_check()

        # Check Redis
        cache = get_cache()
        redis_healthy = cache.health_check()

        if db_healthy and redis_healthy:
            return (
                jsonify(
                    {
                        "status": "ready",
                        "checks": {
                            "database": "healthy",
                            "redis": "healthy",
                        },
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "not ready",
                        "checks": {
                            "database": "healthy" if db_healthy else "unhealthy",
                            "redis": "healthy" if redis_healthy else "unhealthy",
                        },
                    }
                ),
                503,
            )

    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return jsonify({"status": "error", "error": str(e)}), 503
