"""Unit tests for EmotionService monthly statistics."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from application.services.emotion_service import EmotionService
from application.dto.emotion_dto import (
    EmotionStatistic,
    MonthlyStatisticsResponse,
    SentimentStatistic,
)
from domain import EmotionRecord, EmotionType, SentimentType, EmotionScore, UserId, ModelType


@pytest.fixture
def mock_repositories():
    """Create mock repositories."""
    emotion_repo = MagicMock()
    user_repo = MagicMock()
    model_factory = MagicMock()
    cache = MagicMock()

    return emotion_repo, user_repo, model_factory, cache


@pytest.fixture
def emotion_service(mock_repositories):
    """Create EmotionService with mocked dependencies."""
    emotion_repo, user_repo, model_factory, cache = mock_repositories
    return EmotionService(emotion_repo, user_repo, model_factory, cache)


@pytest.fixture
def sample_user():
    """Create a sample user."""
    from domain import User
    return User(
        id=uuid4(),
        user_id=UserId.from_telegram("123456789"),
        created_at=datetime(2026, 1, 1, 0, 0, 0)
    )


@pytest.fixture
def sample_emotions():
    """Create sample emotion records for a month."""
    user_id = uuid4()

    # Create 10 emotions: 5 joy, 3 sadness, 2 anger
    emotions = []

    # 5 joy (positive sentiment)
    for i in range(5):
        emotions.append(EmotionRecord(
            id=uuid4(),
            user_id=user_id,
            text="Test message",
            emotion=EmotionType.JOY,
            sentiment=SentimentType.POSITIVE,
            score=EmotionScore.from_float(0.9),
            model_type=ModelType.GROQ,
            created_at=datetime(2026, 1, i + 1, 10, 0, 0)  # Different days
        ))

    # 3 sadness (negative sentiment)
    for i in range(3):
        emotions.append(EmotionRecord(
            id=uuid4(),
            user_id=user_id,
            text="Test message",
            emotion=EmotionType.SADNESS,
            sentiment=SentimentType.NEGATIVE,
            score=EmotionScore.from_float(0.85),
            model_type=ModelType.GROQ,
            created_at=datetime(2026, 1, i + 6, 10, 0, 0)
        ))

    # 2 anger (negative sentiment)
    for i in range(2):
        emotions.append(EmotionRecord(
            id=uuid4(),
            user_id=user_id,
            text="Test message",
            emotion=EmotionType.ANGER,
            sentiment=SentimentType.NEGATIVE,
            score=EmotionScore.from_float(0.8),
            model_type=ModelType.GROQ,
            created_at=datetime(2026, 1, i + 9, 10, 0, 0)
        ))

    return emotions


class TestEmotionServiceMonthlyStats:
    """Test suite for monthly statistics functionality."""

    def test_get_monthly_statistics_success(
        self, emotion_service, sample_user, sample_emotions, mock_repositories
    ):
        """Test successful monthly statistics calculation."""
        emotion_repo, user_repo, _, _ = mock_repositories

        # Mock repository responses
        user_repo.find_or_create_by_telegram_id.return_value = sample_user
        emotion_repo.find_by_user_and_period.return_value = sample_emotions

        # Call service
        stats = emotion_service.get_monthly_statistics("123456789", "2026-01")

        # Verify calls
        user_repo.find_or_create_by_telegram_id.assert_called_once_with("123456789")
        emotion_repo.find_by_user_and_period.assert_called_once()

        # Verify response
        assert isinstance(stats, MonthlyStatisticsResponse)
        assert stats.period == "2026-01"
        assert stats.total_messages == 10
        assert stats.active_days == 10  # 10 different days

        # Verify emotion breakdown
        assert "joy" in stats.emotions
        assert "sadness" in stats.emotions
        assert "anger" in stats.emotions

        # Check joy statistics
        joy_stat = stats.emotions["joy"]
        assert joy_stat.count == 5
        assert joy_stat.percentage == 50.0
        assert 0.85 <= joy_stat.avg_score <= 0.95

        # Check sentiment distribution
        assert stats.sentiment.positive == 50.0  # 5 positive out of 10
        assert stats.sentiment.negative == 50.0  # 5 negative out of 10

        # Verify dominant emotion
        assert stats.dominant_emotion == "joy"

        # Verify insights exist
        assert len(stats.insights) > 0

    def test_get_monthly_statistics_no_data(
        self, emotion_service, sample_user, mock_repositories
    ):
        """Test monthly statistics with no emotion data."""
        emotion_repo, user_repo, _, _ = mock_repositories

        # Mock empty emotions
        user_repo.find_or_create_by_telegram_id.return_value = sample_user
        emotion_repo.find_by_user_and_period.return_value = []

        # Should raise ValueError
        with pytest.raises(ValueError, match="No emotion data found"):
            emotion_service.get_monthly_statistics("123456789", "2026-01")

    def test_get_monthly_statistics_invalid_month_format(
        self, emotion_service, mock_repositories
    ):
        """Test invalid month format."""
        with pytest.raises(ValueError, match="Invalid month format"):
            emotion_service.get_monthly_statistics("123456789", "2026/01")

        with pytest.raises(ValueError, match="Invalid month format"):
            emotion_service.get_monthly_statistics("123456789", "202601")

        with pytest.raises(ValueError, match="Invalid month format"):
            emotion_service.get_monthly_statistics("123456789", "01-2026")

    def test_get_monthly_statistics_invalid_month_value(
        self, emotion_service, mock_repositories
    ):
        """Test invalid month value (e.g., month 13)."""
        with pytest.raises(ValueError):
            emotion_service.get_monthly_statistics("123456789", "2026-13")

        with pytest.raises(ValueError):
            emotion_service.get_monthly_statistics("123456789", "2026-00")

    def test_generate_insights_positive_month(self, emotion_service):
        """Test insights generation for a positive month."""
        # Mock data: 70% positive
        emotion_stats = {
            "joy": EmotionStatistic(count=7, percentage=70.0, avg_score=0.9)
        }
        sentiment_stats = SentimentStatistic(positive=70.0, negative=20.0, neutral=10.0)

        insights = emotion_service._generate_insights(
            emotion_stats=emotion_stats,
            sentiment_stats=sentiment_stats,
            active_days=25,
            total_days_in_month=31,
            month="2026-01"
        )

        # Should have positive month insight
        assert any("positivo" in i.message.lower() for i in insights)

    def test_generate_insights_challenging_month(self, emotion_service):
        """Test insights generation for a challenging month."""
        # Mock data: 60% negative
        emotion_stats = {
            "sadness": EmotionStatistic(count=6, percentage=60.0, avg_score=0.85)
        }
        sentiment_stats = SentimentStatistic(positive=20.0, negative=60.0, neutral=20.0)

        insights = emotion_service._generate_insights(
            emotion_stats=emotion_stats,
            sentiment_stats=sentiment_stats,
            active_days=15,
            total_days_in_month=31,
            month="2026-01"
        )

        # Should have challenging month insight
        assert any("difficile" in i.message.lower() for i in insights)

    def test_generate_insights_high_consistency(self, emotion_service):
        """Test insights for high consistency (80%+ active days)."""
        emotion_stats = {
            "joy": EmotionStatistic(count=10, percentage=100.0, avg_score=0.9)
        }
        sentiment_stats = SentimentStatistic(positive=100.0, negative=0.0, neutral=0.0)

        insights = emotion_service._generate_insights(
            emotion_stats=emotion_stats,
            sentiment_stats=sentiment_stats,
            active_days=25,  # 25/31 = 80.6%
            total_days_in_month=31,
            month="2026-01"
        )

        # Should have high consistency insight
        assert any("fantastico" in i.message.lower() or "25/31" in i.message for i in insights)

    def test_generate_insights_emotional_variety(self, emotion_service):
        """Test insights for high emotional variety."""
        # 5+ different emotions
        emotion_stats = {
            "joy": EmotionStatistic(count=2, percentage=20.0, avg_score=0.9),
            "sadness": EmotionStatistic(count=2, percentage=20.0, avg_score=0.85),
            "anger": EmotionStatistic(count=2, percentage=20.0, avg_score=0.8),
            "fear": EmotionStatistic(count=2, percentage=20.0, avg_score=0.75),
            "love": EmotionStatistic(count=2, percentage=20.0, avg_score=0.95),
        }
        sentiment_stats = SentimentStatistic(positive=40.0, negative=40.0, neutral=20.0)

        insights = emotion_service._generate_insights(
            emotion_stats=emotion_stats,
            sentiment_stats=sentiment_stats,
            active_days=10,
            total_days_in_month=31,
            month="2026-01"
        )

        # Should have variety insight
        assert any("5 emozioni" in i.message for i in insights)

    def test_get_month_name_italian(self, emotion_service):
        """Test Italian month name conversion."""
        assert emotion_service._get_month_name("2026-01") == "Gennaio"
        assert emotion_service._get_month_name("2026-02") == "Febbraio"
        assert emotion_service._get_month_name("2026-12") == "Dicembre"

    def test_get_month_name_invalid(self, emotion_service):
        """Test invalid month name conversion."""
        # Should return original string
        assert emotion_service._get_month_name("invalid") == "invalid"
        assert emotion_service._get_month_name("2026") == "2026"

    def test_active_days_calculation(
        self, emotion_service, sample_user, mock_repositories
    ):
        """Test that active days are calculated correctly (unique dates)."""
        emotion_repo, user_repo, _, _ = mock_repositories

        user_id = uuid4()

        # Create emotions on same day
        same_day_emotions = [
            EmotionRecord(
                id=uuid4(),
                user_id=user_id,
                text="Test message",
                emotion=EmotionType.JOY,
                sentiment=SentimentType.POSITIVE,
                score=EmotionScore.from_float(0.9),
                model_type=ModelType.GROQ,
                created_at=datetime(2026, 1, 5, 10, 0, 0)
            ),
            EmotionRecord(
                id=uuid4(),
                user_id=user_id,
                text="Test message",
                emotion=EmotionType.SADNESS,
                sentiment=SentimentType.NEGATIVE,
                score=EmotionScore.from_float(0.85),
                model_type=ModelType.GROQ,
                created_at=datetime(2026, 1, 5, 14, 0, 0)  # Same day, different time
            ),
        ]

        user_repo.find_or_create_by_telegram_id.return_value = sample_user
        emotion_repo.find_by_user_and_period.return_value = same_day_emotions

        stats = emotion_service.get_monthly_statistics("123456789", "2026-01")

        # Should count as 1 active day, not 2
        assert stats.active_days == 1
        assert stats.total_messages == 2
