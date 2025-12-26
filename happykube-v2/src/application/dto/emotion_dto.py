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

    emotion: str = Field(..., description="Detected emotion")
    sentiment: str | None = Field(None, description="Detected sentiment (optional)")
    score: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    confidence: str = Field(..., description="Confidence percentage")
    model_type: str = Field(..., description="ML model used")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "emotion": "joy",
                "sentiment": "positive",
                "score": 0.95,
                "confidence": "95%",
                "model_type": "italian_emotion",
            }
        }


class EmotionRecordDTO(BaseModel):
    """DTO for emotion record in reports."""

    id: str = Field(..., description="Record UUID")
    emotion: str = Field(..., description="Emotion label")
    sentiment: str | None = Field(None, description="Sentiment label")
    score: float = Field(..., description="Confidence score")
    confidence: str = Field(..., description="Confidence percentage")
    model_type: str = Field(..., description="Model used")
    created_at: datetime = Field(..., description="Analysis timestamp")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
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
