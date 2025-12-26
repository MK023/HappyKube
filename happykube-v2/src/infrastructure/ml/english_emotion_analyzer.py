"""English emotion analyzer."""

from ...config import settings
from ...domain import EmotionScore, EmotionType, ModelType
from .base_analyzer import BaseAnalyzer


class EnglishEmotionAnalyzer(BaseAnalyzer):
    """
    Analyzer for English emotion classification.

    Uses j-hartmann/emotion-english-distilroberta-base model.
    Classifies into 7 emotions: anger, disgust, fear, joy, neutral, sadness, surprise
    """

    def __init__(self) -> None:
        """Initialize English emotion analyzer."""
        super().__init__(
            model_name=settings.english_emotion_model,
            model_type=ModelType.ENGLISH_EMOTION,
        )

    def analyze(self, text: str) -> tuple[EmotionType, EmotionScore]:
        """
        Analyze English text for emotion.

        Args:
            text: English text input

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
            self.logger.error("English emotion analysis failed", error=str(e), text=text[:50])
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)
