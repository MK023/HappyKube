"""DTOs for emotion data transfer."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EmotionAnalysisRequest(BaseModel):
    """Request DTO for emotion analysis."""

    user_id: str = Field(..., description="Telegram user ID", min_length=1, max_length=64)
    text: str = Field(..., description="Text to analyze", min_length=1, max_length=500)

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "user_id": "123456789",
                "text": "Oggi mi sento molto felice!",
            }
        }


class EmotionAnalysisResponse(BaseModel):
    """Response DTO for emotion analysis."""

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "emotion": "joy",
                "sentiment": "positive",
                "score": 0.95,
                "confidence": "95%",
                "model_type": "italian_emotion",
            }
        }
    }

    emotion: str = Field(..., description="Detected emotion")
    sentiment: str | None = Field(None, description="Detected sentiment (optional)")
    score: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    confidence: str = Field(..., description="Confidence percentage")
    model_type: str = Field(..., description="ML model used")


class EmotionRecordDTO(BaseModel):
    """DTO for emotion record in reports."""

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "emotion": "joy",
                "sentiment": "positive",
                "score": 0.92,
                "confidence": "92%",
                "model_type": "italian_emotion",
                "created_at": "2025-12-26T01:00:00Z",
            }
        }
    }

    id: str = Field(..., description="Record UUID")
    emotion: str = Field(..., description="Emotion label")
    sentiment: str | None = Field(None, description="Sentiment label")
    score: float = Field(..., description="Confidence score")
    confidence: str = Field(..., description="Confidence percentage")
    model_type: str = Field(..., description="Model used")
    created_at: datetime = Field(..., description="Analysis timestamp")


class EmotionReportResponse(BaseModel):
    """Response DTO for emotion reports."""

    user_id: str = Field(..., description="User identifier (hashed)")
    period: str | None = Field(None, description="Report period (if filtered)")
    total_records: int = Field(..., description="Total emotion records")
    emotions: list[EmotionRecordDTO] = Field(..., description="List of emotion records")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "user_id": "abc123...",
                "period": "2025-12",
                "total_records": 42,
                "emotions": [],
            }
        }


class EmotionStatistic(BaseModel):
    """DTO for individual emotion statistics."""

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "count": 15,
                "percentage": 35.7,
                "avg_score": 0.87
            }
        }
    }

    count: int = Field(..., description="Number of occurrences", ge=0)
    percentage: float = Field(..., description="Percentage of total", ge=0.0, le=100.0)
    avg_score: float = Field(..., description="Average confidence score", ge=0.0, le=1.0)


class SentimentStatistic(BaseModel):
    """DTO for sentiment distribution statistics."""

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "positive": 62.5,
                "negative": 20.0,
                "neutral": 17.5
            }
        }
    }

    positive: float = Field(..., description="Positive percentage", ge=0.0, le=100.0)
    negative: float = Field(..., description="Negative percentage", ge=0.0, le=100.0)
    neutral: float = Field(..., description="Neutral percentage", ge=0.0, le=100.0)


class MonthlyInsight(BaseModel):
    """DTO for monthly insight message."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "positive_month",
                "message": "🎉 Gennaio è stato un mese positivo! (62% emozioni positive)",
                "icon": "🎉"
            }
        }
    }

    type: str = Field(..., description="Insight type identifier")
    message: str = Field(..., description="Human-readable insight message")
    icon: str = Field(..., description="Emoji icon representing the insight")


class MonthlyStatisticsResponse(BaseModel):
    """Response DTO for monthly emotion statistics."""

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "user_id": "abc123...",
                "period": "2026-01",
                "total_messages": 87,
                "active_days": 28,
                "emotions": {
                    "joy": {"count": 35, "percentage": 40.2, "avg_score": 0.89},
                    "sadness": {"count": 12, "percentage": 13.8, "avg_score": 0.82}
                },
                "sentiment": {"positive": 62.5, "negative": 20.1, "neutral": 17.4},
                "dominant_emotion": "joy",
                "insights": []
            }
        }
    }

    user_id: str = Field(..., description="User identifier (hashed)")
    period: str = Field(..., description="Month in YYYY-MM format")
    total_messages: int = Field(..., description="Total messages analyzed", ge=0)
    active_days: int = Field(..., description="Days with at least one message", ge=0)
    emotions: dict[str, EmotionStatistic] = Field(..., description="Emotion breakdown")
    sentiment: SentimentStatistic = Field(..., description="Sentiment distribution")
    dominant_emotion: str = Field(..., description="Most frequent emotion")
    insights: list[MonthlyInsight] = Field(..., description="Generated insights")
