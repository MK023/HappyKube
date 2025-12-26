"""API routes."""

from .emotion import emotion_bp
from .health import health_bp

__all__ = [
    "emotion_bp",
    "health_bp",
]
