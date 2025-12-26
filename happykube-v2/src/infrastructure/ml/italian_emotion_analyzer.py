"""Italian emotion analyzer."""

from ...config import settings
from ...domain import EmotionScore, EmotionType, ModelType
from .base_analyzer import BaseAnalyzer


class ItalianEmotionAnalyzer(BaseAnalyzer):
    """
    Analyzer for Italian emotion classification.

    Uses MilaNLProc/feel-it-italian-emotion model.
    Classifies into: anger, joy, sadness, fear
    """

    def __init__(self) -> None:
        """Initialize Italian emotion analyzer."""
        super().__init__(
            model_name=settings.italian_emotion_model,
            model_type=ModelType.ITALIAN_EMOTION,
        )

    def analyze(self, text: str) -> tuple[EmotionType, EmotionScore]:
        """
        Analyze Italian text for emotion.

        Args:
            text: Italian text input

        Returns:
            Tuple of (EmotionType, EmotionScore)
        """
        try:
            results = self.classifier(text)
            label, score = self._get_top_prediction(results)

            emotion = EmotionType.from_label(label)
            emotion_score = EmotionScore.from_float(score)

            return emotion, emotion_score

        except Exception as e:
            self.logger.error("Italian emotion analysis failed", error=str(e), text=text[:50])
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)
