"""Sentiment analyzer."""

from config import settings
from domain import EmotionScore, ModelType, SentimentType
from .base_analyzer import BaseAnalyzer


class SentimentAnalyzer(BaseAnalyzer):
    """
    Sentiment analyzer for Italian text.

    Uses MilaNLProc/feel-it-italian-sentiment model.
    Classifies into: positive, negative, neutral
    """

    def __init__(self) -> None:
        """Initialize sentiment analyzer."""
        super().__init__(
            model_name=settings.sentiment_model,
            model_type=ModelType.SENTIMENT,
        )

    def analyze(self, text: str) -> tuple[SentimentType, EmotionScore]:
        """
        Analyze text for sentiment.

        Args:
            text: Text input

        Returns:
            Tuple of (SentimentType, EmotionScore)
        """
        try:
            results = self.classifier(text)
            label, score = self._get_top_prediction(results)

            sentiment = SentimentType.from_label(label)
            sentiment_score = EmotionScore.from_float(score)

            return sentiment, sentiment_score

        except Exception as e:
            self.logger.error("Sentiment analysis failed", error=str(e), text=text[:50])
            return SentimentType.UNKNOWN, EmotionScore.from_float(0.0)
