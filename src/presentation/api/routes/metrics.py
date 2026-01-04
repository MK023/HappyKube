"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(tags=["monitoring"])

# Define Prometheus metrics
emotion_requests_total = Counter(
    "happykube_emotion_requests_total",
    "Total number of emotion analysis requests",
    ["language", "status"]
)

emotion_analysis_duration = Histogram(
    "happykube_emotion_analysis_duration_seconds",
    "Time spent analyzing emotions",
    ["model_type"]
)

active_users = Gauge(
    "happykube_active_users",
    "Number of active users (7-day window)"
)

api_requests_total = Counter(
    "happykube_api_requests_total",
    "Total number of API requests",
    ["method", "endpoint", "status_code"]
)

telegram_messages_total = Counter(
    "happykube_telegram_messages_total",
    "Total number of Telegram messages processed",
    ["command"]
)


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="""
    Prometheus-compatible metrics endpoint for monitoring.

    **Available Metrics:**
    - `happykube_emotion_requests_total` - Total emotion analysis requests (by language, status)
    - `happykube_emotion_analysis_duration_seconds` - Emotion analysis latency (by model_type)
    - `happykube_active_users` - Active users in 7-day window
    - `happykube_api_requests_total` - API request counts (by method, endpoint, status)
    - `happykube_telegram_messages_total` - Telegram messages processed (by command)

    **Note:** Only available if `PROMETHEUS_ENABLED=true` in environment.
    """,
    responses={
        200: {
            "description": "Prometheus metrics in text format",
            "content": {
                "text/plain; version=0.0.4": {
                    "example": """# HELP happykube_emotion_requests_total Total emotion analysis requests
# TYPE happykube_emotion_requests_total counter
happykube_emotion_requests_total{language="it",status="success"} 1523.0
happykube_emotion_requests_total{language="en",status="success"} 847.0
# HELP happykube_active_users Number of active users
# TYPE happykube_active_users gauge
happykube_active_users 342.0"""
                }
            }
        },
        404: {"description": "Metrics collection disabled"}
    }
)
async def metrics():
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics
    """
    if not settings.prometheus_enabled:
        return Response(
            content="Metrics collection is disabled",
            status_code=404,
            media_type="text/plain"
        )

    # Generate metrics
    metrics_output = generate_latest()

    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )
