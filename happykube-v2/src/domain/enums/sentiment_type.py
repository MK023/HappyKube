"""Sentiment type enumeration."""

from enum import Enum


class SentimentType(str, Enum):
    """Supported sentiment types."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"

    @classmethod
    def from_label(cls, label: str) -> "SentimentType":
        """Convert model output label to SentimentType.

        Args:
            label: Raw label from ML model

        Returns:
            SentimentType enum value
        """
        label_lower = label.lower().strip()
        try:
            return cls(label_lower)
        except ValueError:
            return cls.UNKNOWN
