"""Groq-based emotion and sentiment analyzer using Llama."""

import re

import httpx
from httpx import HTTPStatusError, RequestError

from config import get_logger, get_settings
from domain import EmotionScore, EmotionType, SentimentType
from domain.enums import ModelType

logger = get_logger(__name__)
settings = get_settings()

# Constants
GROQ_DEFAULT_CONFIDENCE = 0.85  # High confidence for Llama 3.3 70B model
GROQ_API_TIMEOUT = 10.0  # API timeout in seconds
MAX_TEXT_LENGTH = 500  # Max text length for analysis


class GroqAnalyzer:
    """
    Emotion and sentiment analyzer using Groq API with Llama 3.3 70B.

    Groq provides free, ultra-fast inference for Llama models.
    Rate limit: 14,400 requests/day (10 req/min average).
    """

    def __init__(self) -> None:
        """Initialize Groq analyzer with connection pooling."""
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = settings.groq_api_key
        self.model = "llama-3.3-70b-versatile"
        self.model_name = "llama-3.3-70b-versatile"
        self.model_type = ModelType.GROQ

        # Create shared HTTP client with connection pooling and HTTP/2
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(GROQ_API_TIMEOUT, connect=5.0),
            limits=httpx.Limits(
                max_connections=5, max_keepalive_connections=3, keepalive_expiry=30.0
            ),
            http2=True,  # HTTP/2 multiplexing for better performance
        )

        logger.info("Initialized Groq analyzer with connection pool", model=self.model)

    async def close(self) -> None:
        """Close HTTP client gracefully."""
        await self._client.aclose()
        logger.info("Groq analyzer HTTP client closed")

    async def analyze_emotion(self, text: str) -> tuple[EmotionType, EmotionScore]:
        """
        Analyze text for emotion using Llama via Groq.

        Args:
            text: Input text (any language)

        Returns:
            Tuple of (EmotionType, EmotionScore)
        """
        try:
            # Truncate text to prevent excessive token usage
            truncated = text[:MAX_TEXT_LENGTH]

            response = await self._client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Analyze the emotion in the user's text. "
                            "Respond with ONLY one word from: "
                            "anger, joy, fear, sadness, love, surprise, neutral",
                        },
                        {"role": "user", "content": truncated},
                    ],
                    "max_tokens": 10,
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            result = response.json()

            # Extract emotion label - take first word, strip punctuation
            raw = result["choices"][0]["message"]["content"].strip().lower()
            label = re.sub(r"[^a-z]", "", raw.split()[0]) if raw.split() else ""

            emotion = EmotionType.from_label(label)
            score = EmotionScore.from_float(GROQ_DEFAULT_CONFIDENCE)

            logger.debug("Groq emotion analysis", emotion=emotion.value, score=str(score))
            return emotion, score

        except HTTPStatusError as e:
            logger.error(
                "Groq emotion API error",
                status_code=e.response.status_code,
            )
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)
        except RequestError as e:
            logger.error("Groq emotion connection error", error=str(e))
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)
        except (KeyError, IndexError, ValueError) as e:
            logger.error("Groq emotion response parsing error", error=str(e))
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)

    async def analyze_sentiment(self, text: str) -> tuple[SentimentType, EmotionScore]:
        """
        Analyze text for sentiment using Llama via Groq.

        Args:
            text: Input text (any language)

        Returns:
            Tuple of (SentimentType, EmotionScore)
        """
        try:
            truncated = text[:MAX_TEXT_LENGTH]

            response = await self._client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Analyze the sentiment in the user's text. "
                            "Respond with ONLY one word: positive, negative, or neutral",
                        },
                        {"role": "user", "content": truncated},
                    ],
                    "max_tokens": 10,
                    "temperature": 0,
                },
            )
            response.raise_for_status()
            result = response.json()

            # Extract sentiment label - take first word, strip punctuation
            raw = result["choices"][0]["message"]["content"].strip().lower()
            label = re.sub(r"[^a-z]", "", raw.split()[0]) if raw.split() else ""

            sentiment = SentimentType.from_label(label)
            score = EmotionScore.from_float(GROQ_DEFAULT_CONFIDENCE)

            logger.debug(
                "Groq sentiment analysis",
                sentiment=sentiment.value,
                score=str(score),
            )
            return sentiment, score

        except HTTPStatusError as e:
            logger.error(
                "Groq sentiment API error",
                status_code=e.response.status_code,
            )
            return SentimentType.UNKNOWN, EmotionScore.from_float(0.0)
        except RequestError as e:
            logger.error("Groq sentiment connection error", error=str(e))
            return SentimentType.UNKNOWN, EmotionScore.from_float(0.0)
        except (KeyError, IndexError, ValueError) as e:
            logger.error("Groq sentiment response parsing error", error=str(e))
            return SentimentType.UNKNOWN, EmotionScore.from_float(0.0)
