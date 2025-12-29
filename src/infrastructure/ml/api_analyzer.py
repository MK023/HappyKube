"""HuggingFace Inference API based analyzer."""

from abc import abstractmethod

import httpx

from config import get_logger, settings
from domain import EmotionScore, EmotionType, ModelType

logger = get_logger(__name__)


class APIAnalyzer:
    """
    Base class for analyzers using HuggingFace Inference API.

    Uses HTTP requests instead of loading models locally, saving RAM.
    """

    def __init__(self, model_name: str, model_type: ModelType) -> None:
        """
        Initialize API-based analyzer.

        Args:
            model_name: HuggingFace model identifier
            model_type: Type of model (for tracking)
        """
        self.model_name = model_name
        self.model_type = model_type
        self.api_url = f"{settings.hf_api_url}/{model_name}"
        self.headers = {"Authorization": f"Bearer {settings.huggingface_token}"}

        logger.info(f"Initialized {model_type.value} API analyzer", model=model_name)

    async def _query_api(self, text: str) -> list[dict]:
        """
        Query HuggingFace Inference API.

        Args:
            text: Input text to analyze

        Returns:
            API response with predictions

        Raises:
            httpx.HTTPError: If API request fails
        """
        payload = {"inputs": text}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                logger.debug(
                    f"{self.model_type.value} API response",
                    model=self.model_name,
                    status=response.status_code
                )

                return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"{self.model_type.value} API HTTP error",
                status=e.response.status_code,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error(f"{self.model_type.value} API error", error=str(e))
            raise

    @abstractmethod
    async def analyze(self, text: str) -> tuple[EmotionType | str, EmotionScore]:
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
        Extract top prediction from API response.

        Args:
            results: API response

        Returns:
            Tuple of (label, score)
        """
        if not results or not isinstance(results, list):
            logger.warning("Unexpected API response format", results=str(results)[:100])
            return "unknown", 0.0

        # API returns list of predictions, get the one with highest score
        top = max(results, key=lambda x: x.get("score", 0))
        return top.get("label", "unknown"), top.get("score", 0.0)
