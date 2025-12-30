"""Emotion type enumeration."""

from enum import Enum


class EmotionType(str, Enum):
    """Supported emotion types."""

    # Italian emotion model labels
    ANGER = "anger"
    JOY = "joy"
    SADNESS = "sadness"
    FEAR = "fear"

    # Additional emotion labels (supported by Groq)
    LOVE = "love"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    NEUTRAL = "neutral"

    # Unknown/error state
    UNKNOWN = "unknown"

    @classmethod
    def from_label(cls, label: str) -> "EmotionType":
        """Convert model output label to EmotionType.

        Args:
            label: Raw label from ML model

        Returns:
            EmotionType enum value
        """
        label_lower = label.lower().strip()
        try:
            return cls(label_lower)
        except ValueError:
            return cls.UNKNOWN

    @property
    def is_negative(self) -> bool:
        """Check if emotion is negative."""
        return self in {self.ANGER, self.SADNESS, self.FEAR, self.DISGUST}

    @property
    def is_positive(self) -> bool:
        """Check if emotion is positive."""
        return self in {self.JOY, self.LOVE, self.SURPRISE}

    @property
    def is_neutral(self) -> bool:
        """Check if emotion is neutral."""
        return self in {self.NEUTRAL, self.UNKNOWN}
