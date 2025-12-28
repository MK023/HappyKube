"""Base class for ML analyzers."""

from abc import ABC, abstractmethod

from transformers import pipeline

from ...config import get_logger
from ...domain import EmotionScore, EmotionType, ModelType

logger = get_logger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for emotion/sentiment analyzers.

    All ML model wrappers inherit from this.
    """

    def __init__(self, model_name: str, model_type: ModelType) -> None:
        """
        Initialize analyzer with Hugging Face model.

        Args:
            model_name: HuggingFace model identifier
            model_type: Type of model (for tracking)
        """
        self.model_name = model_name
        self.model_type = model_type

        logger.info(f"Loading {model_type.value} model", model=model_name)

        try:
            self.classifier = pipeline(
                "text-classification",
                model=model_name,
                return_all_scores=True,  # Get all emotion scores
            )
            logger.info(f"{model_type.value} model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load {model_type.value} model", error=str(e))
            raise

    @abstractmethod
    def analyze(self, text: str) -> tuple[EmotionType | str, EmotionScore]:
        """
        Analyze text and return emotion/sentiment with score.

        Args:
            text: Input text

        Returns:
            Tuple of (emotion/sentiment, confidence score)
        """
        pass

    def _get_top_prediction(self, results: list) -> tuple[str, float]:
        """
        Extract top prediction from model output.

        Args:
            results: Model output

        Returns:
            Tuple of (label, score)
        """
        if not results or not isinstance(results[0], list):
            logger.warning("Unexpected model output format", results=str(results)[:100])
            return "unknown", 0.0

        scores = results[0]
        top = max(scores, key=lambda x: x["score"])
        return top["label"], top["score"]
