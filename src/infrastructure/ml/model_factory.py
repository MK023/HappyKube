"""ML model factory for dependency injection."""

from config import get_logger, settings
from .api_analyzer import APIAnalyzer
from .english_emotion_analyzer import EnglishEmotionAnalyzer
from .italian_emotion_analyzer import ItalianEmotionAnalyzer
from .language_detector import detect_language
from .sentiment_analyzer import SentimentAnalyzer

# Import external AI analyzers if API keys are configured
if settings.anthropic_api_key:
    from .claude_analyzer import ClaudeAnalyzer
if settings.groq_api_key:
    from .groq_analyzer import GroqAnalyzer

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
        self._claude: "ClaudeAnalyzer | None" = None  # type: ignore
        self._groq: "GroqAnalyzer | None" = None  # type: ignore

    def get_groq_analyzer(self) -> "GroqAnalyzer":  # type: ignore
        """
        Get Groq analyzer (cached). Only available if GROQ_API_KEY is set.

        Returns:
            GroqAnalyzer instance
        """
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not configured")

        if self._groq is None:
            logger.info("Creating Groq analyzer")
            self._groq = GroqAnalyzer()  # type: ignore
        return self._groq  # type: ignore

    def get_claude_analyzer(self) -> "ClaudeAnalyzer":  # type: ignore
        """
        Get Claude analyzer (cached). Only available if ANTHROPIC_API_KEY is set.

        Returns:
            ClaudeAnalyzer instance
        """
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        if self._claude is None:
            logger.info("Creating Claude analyzer")
            self._claude = ClaudeAnalyzer()  # type: ignore
        return self._claude  # type: ignore

    def get_italian_emotion_analyzer(self) -> ItalianEmotionAnalyzer:
        """
        Get Italian emotion analyzer (cached).
        Falls back to Claude if configured.

        Returns:
            ItalianEmotionAnalyzer instance
        """
        # Priority: Groq (free) > Claude (paid) > HF API (deprecated)
        if settings.groq_api_key:
            return self.get_groq_analyzer()  # type: ignore
        if settings.anthropic_api_key:
            return self.get_claude_analyzer()  # type: ignore

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
        Falls back to Claude if configured.

        Returns:
            SentimentAnalyzer instance
        """
        # Priority: Groq (free) > Claude (paid) > HF API (deprecated)
        if settings.groq_api_key:
            return self.get_groq_analyzer()  # type: ignore
        if settings.anthropic_api_key:
            return self.get_claude_analyzer()  # type: ignore

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
