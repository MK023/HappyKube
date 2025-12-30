"""ML model factory for Groq analyzer."""

from config import get_logger, settings
from .groq_analyzer import GroqAnalyzer

logger = get_logger(__name__)


class ModelFactory:
    """
    Factory for creating and caching Groq analyzer instance.

    Uses Llama 3.3 70B via Groq API for all emotion and sentiment analysis.
    """

    def __init__(self) -> None:
        """Initialize factory with empty cache."""
        self._groq: GroqAnalyzer | None = None

    def get_groq_analyzer(self) -> GroqAnalyzer:
        """
        Get Groq analyzer (cached singleton).

        Returns:
            GroqAnalyzer instance

        Raises:
            ValueError: If GROQ_API_KEY not configured
        """
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured in environment")

        if self._groq is None:
            logger.info("Creating Groq analyzer")
            self._groq = GroqAnalyzer()
        return self._groq

    # Backward compatibility aliases
    def get_italian_emotion_analyzer(self) -> GroqAnalyzer:
        """Get emotion analyzer (uses Groq)."""
        return self.get_groq_analyzer()

    def get_english_emotion_analyzer(self) -> GroqAnalyzer:
        """Get emotion analyzer (uses Groq)."""
        return self.get_groq_analyzer()

    def get_sentiment_analyzer(self) -> GroqAnalyzer:
        """Get sentiment analyzer (uses Groq)."""
        return self.get_groq_analyzer()

    def get_emotion_analyzer_for_text(self, text: str) -> GroqAnalyzer:
        """
        Get emotion analyzer for any text (uses Groq, supports all languages).

        Args:
            text: Input text in any language

        Returns:
            GroqAnalyzer instance
        """
        return self.get_groq_analyzer()


# Global singleton factory
_factory: ModelFactory | None = None


def get_model_factory() -> ModelFactory:
    """
    Get global model factory instance.

    Returns:
        ModelFactory singleton
    """
    global _factory
    if _factory is None:
        logger.info("Initializing model factory")
        _factory = ModelFactory()
    return _factory
