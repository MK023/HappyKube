"""Italian emotion analyzer."""

from config import get_logger, settings
from domain import EmotionScore, EmotionType, ModelType
from .api_analyzer import APIAnalyzer

logger = get_logger(__name__)


class ItalianEmotionAnalyzer(APIAnalyzer):
    """
    Analyzer for multilingual emotion classification.

    Uses MilaNLProc/xlm-emo-t model via HF Inference API.
    Supports 19 languages including Italian and English.
    Classifies into: anger, joy, sadness, fear
    """

    def __init__(self) -> None:
        """Initialize multilingual emotion analyzer."""
        super().__init__(
            model_name=settings.emotion_model,
            model_type=ModelType.ITALIAN_EMOTION,
        )

    async def analyze(self, text: str) -> tuple[EmotionType, EmotionScore]:
        """
        Analyze text for emotion (supports 19 languages).

        Args:
            text: Input text in any supported language

        Returns:
            Tuple of (EmotionType, EmotionScore)
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

            emotion = EmotionType.from_label(label)
            emotion_score = EmotionScore.from_float(score)

            return emotion, emotion_score

        except Exception as e:
            logger.error("Multilingual emotion analysis failed", error=str(e), text=text[:50])
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)
