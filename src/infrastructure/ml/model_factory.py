"""ML model factory for Groq analyzer."""

from config import get_logger, settings
from .groq_analyzer import GroqAnalyzer

logger = get_logger(__name__)


class ModelFactory:
    """Factory for creating and caching Groq analyzer instance."""

    def __init__(self) -> None:
        """Initialize factory with empty cache."""
        self._groq: GroqAnalyzer | None = None

    def get_groq_analyzer(self) -> GroqAnalyzer:
        """Get Groq analyzer (cached singleton)."""
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured in environment")

        if self._groq is None:
            logger.info("Creating Groq analyzer")
            self._groq = GroqAnalyzer()
        return self._groq


# Global singleton
_factory: ModelFactory | None = None


def get_model_factory() -> ModelFactory:
    """Get global model factory instance."""
    global _factory
    if _factory is None:
        logger.info("Initializing model factory")
        _factory = ModelFactory()
    return _factory
