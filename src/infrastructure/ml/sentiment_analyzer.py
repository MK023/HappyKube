"""Sentiment analyzer."""

from config import get_logger, settings
from domain import EmotionScore, ModelType, SentimentType
from .api_analyzer import APIAnalyzer

logger = get_logger(__name__)


class SentimentAnalyzer(APIAnalyzer):
    """
    Sentiment analyzer for Italian text.

    Uses MilaNLProc/feel-it-italian-sentiment model via HF Inference API.
    Classifies into: positive, negative, neutral
    """

    def __init__(self) -> None:
        """Initialize sentiment analyzer."""
        super().__init__(
            model_name=settings.sentiment_model,
            model_type=ModelType.SENTIMENT,
        )

    async def analyze(self, text: str) -> tuple[SentimentType, EmotionScore]:
        """
        Analyze text for sentiment.

        Args:
            text: Text input

        Returns:
            Tuple of (SentimentType, EmotionScore)
        """
        try:
            results = await self._query_api(text)

            # API returns a list of scores for each label
            if results and isinstance(results, list) and len(results) > 0:
                # If nested list (some models return [[{...}]])
                if isinstance(results[0], list):
                    results = results[0]

                label, score = self._get_top_prediction(results)
            else:
                label, score = "unknown", 0.0

            sentiment = SentimentType.from_label(label)
            sentiment_score = EmotionScore.from_float(score)

            return sentiment, sentiment_score

        except Exception as e:
            logger.error("Sentiment analysis failed", error=str(e), text=text[:50])
            return SentimentType.UNKNOWN, EmotionScore.from_float(0.0)
