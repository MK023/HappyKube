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

    async def _query_api(self, text: str, max_retries: int = 3) -> list[dict]:
        """
        Query HuggingFace Inference API with retry logic.

        Args:
            text: Input text to analyze
            max_retries: Maximum number of retry attempts

        Returns:
            API response with predictions

        Raises:
            httpx.HTTPError: If API request fails after all retries
        """
        payload = {"inputs": text}
        last_error = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    result = response.json()

                    if attempt > 0:
                        logger.info(
                            f"{self.model_type.value} API retry successful",
                            attempt=attempt + 1,
                            model=self.model_name
                        )

                    logger.debug(
                        f"{self.model_type.value} API response",
                        model=self.model_name,
                        status=response.status_code
                    )

                    return result

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                # Don't retry on client errors (4xx), only server errors (5xx) and rate limits
                if status_code < 500 and status_code != 429:
                    logger.error(
                        f"{self.model_type.value} API client error - not retrying",
                        status=status_code,
                        error=str(e)
                    )
                    raise

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"{self.model_type.value} API error, retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time,
                        status=status_code
                    )
                    import asyncio
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"{self.model_type.value} API failed after retries",
                        attempts=max_retries,
                        status=status_code
                    )

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"{self.model_type.value} API error, retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    import asyncio
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(
                        f"{self.model_type.value} API failed after retries",
                        attempts=max_retries,
                        error=str(e)
                    )

        # If we get here, all retries failed
        raise last_error if last_error else Exception("API request failed")

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
