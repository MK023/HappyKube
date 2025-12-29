"""ML model factory for dependency injection."""

from config import get_logger
from .api_analyzer import APIAnalyzer
from .english_emotion_analyzer import EnglishEmotionAnalyzer
from .italian_emotion_analyzer import ItalianEmotionAnalyzer
from .language_detector import detect_language
from .sentiment_analyzer import SentimentAnalyzer

logger = get_logger(__name__)


class ModelFactory:
    """
    Factory for creating and caching ML model instances.

    Implements lazy loading and singleton pattern for each model type.
    """

    def __init__(self) -> None:
        """Initialize factory with empty cache."""
        self._italian_emotion: ItalianEmotionAnalyzer | None = None
        self._english_emotion: EnglishEmotionAnalyzer | None = None
        self._sentiment: SentimentAnalyzer | None = None

    def get_italian_emotion_analyzer(self) -> ItalianEmotionAnalyzer:
        """
        Get Italian emotion analyzer (cached).

        Returns:
            ItalianEmotionAnalyzer instance
        """
        if self._italian_emotion is None:
            logger.info("Creating Italian emotion analyzer")
            self._italian_emotion = ItalianEmotionAnalyzer()
        return self._italian_emotion

    def get_english_emotion_analyzer(self) -> EnglishEmotionAnalyzer:
        """
        Get English emotion analyzer (cached).

        Returns:
            EnglishEmotionAnalyzer instance
        """
        if self._english_emotion is None:
            logger.info("Creating English emotion analyzer")
            self._english_emotion = EnglishEmotionAnalyzer()
        return self._english_emotion

    def get_sentiment_analyzer(self) -> SentimentAnalyzer:
        """
        Get sentiment analyzer (cached).

        Returns:
            SentimentAnalyzer instance
        """
        if self._sentiment is None:
            logger.info("Creating sentiment analyzer")
            self._sentiment = SentimentAnalyzer()
        return self._sentiment

    def get_emotion_analyzer_for_text(self, text: str) -> APIAnalyzer:
        """
        Get appropriate emotion analyzer based on text language.

        Args:
            text: Input text

        Returns:
            Italian or English emotion analyzer
        """
        language = detect_language(text)

        if language == "italian":
            return self.get_italian_emotion_analyzer()
        else:
            return self.get_english_emotion_analyzer()


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
