"""Emotion analysis service (business logic layer)."""

from datetime import datetime
from uuid import UUID

from config import get_logger
from domain import EmotionRecord, ModelType
from infrastructure.cache import RedisCache
from infrastructure.ml import ModelFactory
from ..dto.emotion_dto import (
    EmotionAnalysisResponse,
    EmotionRecordDTO,
    EmotionReportResponse,
)
from ..interfaces.emotion_repository import IEmotionRepository
from ..interfaces.user_repository import IUserRepository

logger = get_logger(__name__)


class EmotionService:
    """
    Service for emotion analysis operations.

    Orchestrates ML models, caching, and persistence.
    """

    def __init__(
        self,
        emotion_repo: IEmotionRepository,
        user_repo: IUserRepository,
        model_factory: ModelFactory,
        cache: RedisCache,
    ) -> None:
        """
        Initialize emotion service with dependencies.

        Args:
            emotion_repo: Emotion repository
            user_repo: User repository
            model_factory: ML model factory
            cache: Redis cache
        """
        self.emotion_repo = emotion_repo
        self.user_repo = user_repo
        self.model_factory = model_factory
        self.cache = cache

    async def analyze_emotion(self, telegram_id: str, text: str) -> EmotionAnalysisResponse:
        """
        Analyze emotion from text with caching.

        Args:
            telegram_id: Telegram user ID
            text: Text to analyze

        Returns:
            EmotionAnalysisResponse DTO
        """
        # Check cache first (same text = same result)
        cache_key = f"emotion:{telegram_id}:{hash(text)}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("Returning cached emotion analysis", telegram_id=telegram_id)
            return EmotionAnalysisResponse(**cached)

        # Find or create user
        user = self.user_repo.find_or_create_by_telegram_id(telegram_id)

        # Get appropriate analyzer based on language
        emotion_analyzer = self.model_factory.get_emotion_analyzer_for_text(text)
        sentiment_analyzer = self.model_factory.get_sentiment_analyzer()

        # Perform analysis (async API calls)
        emotion, emotion_score = await emotion_analyzer.analyze(text)
        sentiment, sentiment_score = await sentiment_analyzer.analyze(text)

        logger.info(
            "Emotion analyzed",
            user_id=str(user.id),
            emotion=emotion.value,
            score=emotion_score.to_float(),
            model=emotion_analyzer.model_type.value,
        )

        # Save to database
        emotion_record = EmotionRecord.create(
            user_id=user.id,
            text=text,
            emotion=emotion,
            score=emotion_score,
            model_type=emotion_analyzer.model_type,
            sentiment=sentiment,
            metadata={
                "model_name": emotion_analyzer.model_name,
                "sentiment_score": sentiment_score.to_float(),
            },
        )

        self.emotion_repo.save(emotion_record)

        # Prepare response
        response = EmotionAnalysisResponse(
            emotion=emotion.value,
            sentiment=sentiment.value if sentiment else None,
            score=emotion_score.to_float(),
            confidence=str(emotion_score),
            model_type=emotion_analyzer.model_type.value,
        )

        # Cache for 1 hour
        self.cache.set(cache_key, response.model_dump(), ttl=3600)

        return response

    def get_user_report(
        self,
        telegram_id: str,
        month: str | None = None,
    ) -> EmotionReportResponse:
        """
        Get emotion report for user.

        Args:
            telegram_id: Telegram user ID
            month: Optional month filter (format: YYYY-MM)

        Returns:
            EmotionReportResponse DTO
        """
        # Find user
        user = self.user_repo.find_or_create_by_telegram_id(telegram_id)

        # Parse month filter if provided
        if month:
            try:
                # Parse YYYY-MM
                year, mon = map(int, month.split("-"))
                start_date = datetime(year, mon, 1)

                # Calculate end of month
                if mon == 12:
                    end_date = datetime(year + 1, 1, 1)
                else:
                    end_date = datetime(year, mon + 1, 1)

                emotions = self.emotion_repo.find_by_user_and_period(
                    user.id, start_date, end_date
                )
                period_label = month
            except ValueError:
                logger.warning("Invalid month format", month=month)
                # Fall back to all emotions
                emotions = self.emotion_repo.find_by_user(user.id, limit=1000)
                period_label = None
        else:
            # Get all emotions (limited to last 1000)
            emotions = self.emotion_repo.find_by_user(user.id, limit=1000)
            period_label = None

        # Convert to DTOs
        emotion_dtos = [
            EmotionRecordDTO(
                id=str(e.id),
                emotion=e.emotion.value,
                sentiment=e.sentiment.value if e.sentiment else None,
                score=e.score.to_float(),
                confidence=str(e.score),
                model_type=e.model_type.value,
                created_at=e.created_at,
            )
            for e in emotions
        ]

        return EmotionReportResponse(
            user_id=user.user_id.hashed_id[:16],  # Partial hash for privacy
            period=period_label,
            total_records=len(emotion_dtos),
            emotions=emotion_dtos,
        )
