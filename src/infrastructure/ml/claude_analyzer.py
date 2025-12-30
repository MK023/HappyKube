"""Claude-based emotion and sentiment analyzer."""

import anthropic

from config import get_logger, settings
from domain import EmotionScore, EmotionType, SentimentType

logger = get_logger(__name__)


class ClaudeAnalyzer:
    """
    Emotion and sentiment analyzer using Claude API.

    Uses Claude Sonnet 4 for zero-shot classification.
    More accurate than small models, minimal RAM usage.
    """

    def __init__(self) -> None:
        """Initialize Claude analyzer."""
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = "claude-sonnet-4-20250514"
        logger.info("Initialized Claude analyzer", model=self.model)

    async def analyze_emotion(self, text: str) -> tuple[EmotionType, EmotionScore]:
        """
        Analyze text for emotion using Claude.

        Args:
            text: Input text (any language)

        Returns:
            Tuple of (EmotionType, EmotionScore)
        """
        try:
            prompt = f"""Analyze the emotion in this text. Respond with ONLY one word from: anger, joy, fear, sadness, love, surprise, neutral

Text: {text}

Emotion:"""

            message = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract emotion label
            label = message.content[0].text.strip().lower()

            # Claude doesn't provide confidence, use fixed high score
            emotion = EmotionType.from_label(label)
            score = EmotionScore.from_float(0.85)  # High confidence for Claude

            logger.debug("Claude emotion analysis", text=text[:50], emotion=emotion.value, score=str(score))
            return emotion, score

        except Exception as e:
            logger.error("Claude emotion analysis failed", error=str(e), text=text[:50])
            return EmotionType.UNKNOWN, EmotionScore.from_float(0.0)

    async def analyze_sentiment(self, text: str) -> tuple[SentimentType, EmotionScore]:
        """
        Analyze text for sentiment using Claude.

        Args:
            text: Input text (any language)

        Returns:
            Tuple of (SentimentType, EmotionScore)
        """
        try:
            prompt = f"""Analyze the sentiment in this text. Respond with ONLY one word: positive, negative, or neutral

Text: {text}

Sentiment:"""

            message = await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract sentiment label
            label = message.content[0].text.strip().lower()

            sentiment = SentimentType.from_label(label)
            score = EmotionScore.from_float(0.85)  # High confidence for Claude

            logger.debug("Claude sentiment analysis", text=text[:50], sentiment=sentiment.value, score=str(score))
            return sentiment, score

        except Exception as e:
            logger.error("Claude sentiment analysis failed", error=str(e), text=text[:50])
            return SentimentType.UNKNOWN, EmotionScore.from_float(0.0)
