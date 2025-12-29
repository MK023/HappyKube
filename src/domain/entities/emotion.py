"""Emotion domain entity."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from ..enums.emotion_type import EmotionType
from ..enums.model_type import ModelType
from ..enums.sentiment_type import SentimentType
from ..value_objects.emotion_score import EmotionScore


@dataclass
class EmotionRecord:
    """Emotion analysis record entity.

    Attributes:
        id: Internal UUID (primary key)
        user_id: Reference to User UUID
        text: Original user text (will be encrypted at persistence layer)
        emotion: Detected emotion type
        sentiment: Detected sentiment type (optional)
        score: Confidence score
        model_type: ML model used for analysis
        created_at: Analysis timestamp
        metadata: Additional metadata (model version, etc.)
    """

    id: UUID
    user_id: UUID
    text: str
    emotion: EmotionType
    sentiment: SentimentType | None
    score: EmotionScore
    model_type: ModelType
    created_at: datetime
    metadata: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        user_id: UUID,
        text: str,
        emotion: EmotionType | str,
        score: EmotionScore | float,
        model_type: ModelType | str,
        sentiment: SentimentType | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "EmotionRecord":
        """Factory method to create a new emotion record.

        Args:
            user_id: User UUID
            text: Original text input
            emotion: Emotion type or label
            score: Confidence score
            model_type: Model type or string
            sentiment: Optional sentiment type or label
            metadata: Optional additional metadata

        Returns:
            New EmotionRecord instance
        """
        # Convert string types to enums if needed
        if isinstance(emotion, str):
            emotion = EmotionType.from_label(emotion)

        if isinstance(model_type, str):
            model_type = ModelType(model_type)

        if isinstance(score, (float, int)):
            score = EmotionScore.from_float(score)

        if isinstance(sentiment, str):
            sentiment = SentimentType.from_label(sentiment)

        return cls(
            id=uuid4(),
            user_id=user_id,
            text=text,
            emotion=emotion,
            sentiment=sentiment,
            score=score,
            model_type=model_type,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )

    @property
    def is_high_confidence(self) -> bool:
        """Check if analysis has high confidence."""
        return self.score.is_high_confidence

    @property
    def is_negative_emotion(self) -> bool:
        """Check if emotion is negative."""
        return self.emotion.is_negative

    @property
    def is_positive_emotion(self) -> bool:
        """Check if emotion is positive."""
        return self.emotion.is_positive

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dict representation (for API responses)
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "emotion": self.emotion.value,
            "sentiment": self.sentiment.value if self.sentiment else None,
            "score": self.score.to_float(),
            "confidence": str(self.score),
            "model_type": self.model_type.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"EmotionRecord(id={self.id}, emotion={self.emotion.value}, "
            f"score={self.score}, model={self.model_type.value})"
        )
