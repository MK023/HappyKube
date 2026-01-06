"""Emotion analysis service (business logic layer)."""

import asyncio
import hashlib
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
    EmotionStatistic,
    MonthlyInsight,
    MonthlyStatisticsResponse,
    SentimentStatistic,
)
from ..interfaces.emotion_repository import IEmotionRepository
from ..interfaces.user_repository import IUserRepository

logger = get_logger(__name__)

# Cache TTL configuration (in seconds)
CACHE_TTL_EMOTION = 7200  # 2 hours - same text will have same emotion
CACHE_TTL_MONTHLY = 1800  # 30 minutes - stats update frequently


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
        # Use SHA256 hash (shortened to 16 chars for memory efficiency)
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        cache_key = f"emo:{telegram_id[:8]}:{text_hash}"  # Shorter keys = less Redis memory
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("Returning cached emotion analysis", telegram_id=telegram_id)
            return EmotionAnalysisResponse(**cached)

        # Find or create user
        user = self.user_repo.find_or_create_by_telegram_id(telegram_id)

        # Get Groq analyzer (handles all languages)
        analyzer = self.model_factory.get_groq_analyzer()

        # Perform analysis (async API calls in parallel for speed)
        (emotion, emotion_score), (sentiment, sentiment_score) = await asyncio.gather(
            analyzer.analyze_emotion(text),
            analyzer.analyze_sentiment(text)
        )

        logger.info(
            "Emotion analyzed",
            user_id=str(user.id),
            emotion=emotion.value,
            score=emotion_score.to_float(),
            model=analyzer.model_type.value,
        )

        # Save to database
        emotion_record = EmotionRecord.create(
            user_id=user.id,
            text=text,
            emotion=emotion,
            score=emotion_score,
            model_type=analyzer.model_type,
            sentiment=sentiment,
            metadata={
                "model_name": analyzer.model_name,
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
            model_type=analyzer.model_type.value,
        )

        # Cache for 2 hours (longer TTL for stable emotion analysis)
        self.cache.set(cache_key, response.model_dump(), ttl=CACHE_TTL_EMOTION)

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

    def get_monthly_statistics(
        self,
        telegram_id: str,
        month: str,
    ) -> MonthlyStatisticsResponse:
        """
        Calculate monthly emotion statistics with insights.

        Args:
            telegram_id: Telegram user ID
            month: Month in YYYY-MM format

        Returns:
            MonthlyStatisticsResponse with complete statistics

        Raises:
            ValueError: If month format is invalid or no data found
        """
        # Validate month format
        try:
            year, mon = map(int, month.split("-"))
            if not (1 <= mon <= 12):
                raise ValueError("Month must be between 01 and 12")
            start_date = datetime(year, mon, 1)
        except (ValueError, AttributeError) as e:
            logger.error("Invalid month format", month=month, error=str(e))
            raise ValueError(f"Invalid month format. Use YYYY-MM (e.g., 2026-01)") from e

        # Calculate end of month
        if mon == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, mon + 1, 1)

        # Find user
        user = self.user_repo.find_or_create_by_telegram_id(telegram_id)

        # Get emotions for the month
        emotions = self.emotion_repo.find_by_user_and_period(
            user.id, start_date, end_date
        )

        if not emotions:
            logger.info("No emotions found for month", user_id=str(user.id), month=month)
            raise ValueError(f"No emotion data found for {month}")

        total = len(emotions)

        # Calculate active days (unique dates)
        active_days = len(set(e.created_at.date() for e in emotions))

        # Count emotions and scores
        emotion_counts: dict[str, list[float]] = {}  # emotion -> list of scores
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}

        for e in emotions:
            # Emotion aggregation
            if e.emotion.value not in emotion_counts:
                emotion_counts[e.emotion.value] = []
            emotion_counts[e.emotion.value].append(e.score.to_float())

            # Sentiment aggregation
            if e.sentiment:
                sentiment_counts[e.sentiment.value] += 1

        # Build emotion statistics
        emotion_stats: dict[str, EmotionStatistic] = {}
        for emotion, scores in emotion_counts.items():
            count = len(scores)
            percentage = round(count / total * 100, 1)
            avg_score = round(sum(scores) / count, 2)

            emotion_stats[emotion] = EmotionStatistic(
                count=count,
                percentage=percentage,
                avg_score=avg_score
            )

        # Build sentiment statistics
        sentiment_total = sum(sentiment_counts.values())
        pos_pct = (
            round(sentiment_counts["positive"] / sentiment_total * 100, 1)
            if sentiment_total > 0
            else 0.0
        )
        neg_pct = (
            round(sentiment_counts["negative"] / sentiment_total * 100, 1)
            if sentiment_total > 0
            else 0.0
        )
        neu_pct = (
            round(sentiment_counts["neutral"] / sentiment_total * 100, 1)
            if sentiment_total > 0
            else 0.0
        )
        sentiment_stats = SentimentStatistic(
            positive=pos_pct, negative=neg_pct, neutral=neu_pct
        )

        # Find dominant emotion
        dominant_emotion = max(emotion_stats.items(), key=lambda x: x[1].count)[0]

        # Generate insights
        insights = self._generate_insights(
            emotion_stats=emotion_stats,
            sentiment_stats=sentiment_stats,
            active_days=active_days,
            total_days_in_month=(end_date - start_date).days,
            month=month
        )

        logger.info(
            "Monthly statistics calculated",
            user_id=str(user.id),
            month=month,
            total_messages=total,
            dominant_emotion=dominant_emotion
        )

        return MonthlyStatisticsResponse(
            user_id=user.user_id.hashed_id[:16],
            period=month,
            total_messages=total,
            active_days=active_days,
            emotions=emotion_stats,
            sentiment=sentiment_stats,
            dominant_emotion=dominant_emotion,
            insights=insights
        )

    def _generate_insights(
        self,
        emotion_stats: dict[str, EmotionStatistic],
        sentiment_stats: SentimentStatistic,
        active_days: int,
        total_days_in_month: int,
        month: str
    ) -> list[MonthlyInsight]:
        """
        Generate actionable insights from statistics.

        Args:
            emotion_stats: Emotion breakdown
            sentiment_stats: Sentiment distribution
            active_days: Days with activity
            total_days_in_month: Total days in the month
            month: Month identifier (YYYY-MM)

        Returns:
            List of insights with icons and messages
        """
        insights: list[MonthlyInsight] = []

        # Insight 1: Overall sentiment
        month_name = self._get_month_name(month)
        if sentiment_stats.positive > 60:
            msg = (
                f"🎉 {month_name} è stato un mese positivo! "
                f"({sentiment_stats.positive}% emozioni positive)"
            )
            insights.append(MonthlyInsight(type="positive_month", message=msg, icon="🎉"))
        elif sentiment_stats.negative > 50:
            msg = (
                f"💪 {month_name} è stato difficile, ma ce l'hai fatta! "
                f"({sentiment_stats.negative}% emozioni negative)"
            )
            insights.append(
                MonthlyInsight(type="challenging_month", message=msg, icon="💪")
            )
        else:
            insights.append(MonthlyInsight(
                type="balanced_month",
                message=f"⚖️ {self._get_month_name(month)} è stato un mese equilibrato",
                icon="⚖️"
            ))

        # Insight 2: Dominant emotion
        from domain.enums.emotion_emojis import EMOTION_EMOJIS

        dominant = max(emotion_stats.items(), key=lambda x: x[1].percentage)
        icon = EMOTION_EMOJIS.get(dominant[0], "💭")
        insights.append(MonthlyInsight(
            type="dominant_emotion",
            message=f"{icon} Emozione più frequente: {dominant[0]} ({dominant[1].percentage}%)",
            icon=icon
        ))

        # Insight 3: Consistency
        consistency_pct = round(active_days / total_days_in_month * 100, 1)
        if consistency_pct >= 80:
            msg = (
                f"🔥 Fantastico! Hai registrato emozioni per "
                f"{active_days}/{total_days_in_month} giorni ({consistency_pct}%)"
            )
            insights.append(MonthlyInsight(type="high_consistency", message=msg, icon="🔥"))
        elif consistency_pct >= 50:
            insights.append(MonthlyInsight(
                type="good_consistency",
                message=f"👍 Buona costanza: {active_days}/{total_days_in_month} giorni attivi",
                icon="👍"
            ))

        # Insight 4: Emotional variety
        num_emotions = len(emotion_stats)
        if num_emotions >= 5:
            insights.append(MonthlyInsight(
                type="high_variety",
                message=f"🌈 Hai sperimentato {num_emotions} emozioni diverse questo mese",
                icon="🌈"
            ))

        return insights

    @staticmethod
    def _get_month_name(month: str) -> str:
        """Convert YYYY-MM to Italian month name."""
        month_names = {
            "01": "Gennaio", "02": "Febbraio", "03": "Marzo",
            "04": "Aprile", "05": "Maggio", "06": "Giugno",
            "07": "Luglio", "08": "Agosto", "09": "Settembre",
            "10": "Ottobre", "11": "Novembre", "12": "Dicembre"
        }
        try:
            _, mon = month.split("-")
            return month_names.get(mon, month)
        except (ValueError, KeyError):
            return month
