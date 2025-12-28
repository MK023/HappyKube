"""Emotion score value object."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EmotionScore:
    """Immutable value object representing an emotion confidence score.

    Attributes:
        value: Confidence score between 0.0 and 1.0
    """

    value: Decimal

    def __post_init__(self) -> None:
        """Validate score value."""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

        if not (Decimal("0.0") <= self.value <= Decimal("1.0")):
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.value}")

    @classmethod
    def from_float(cls, score: float) -> "EmotionScore":
        """Create EmotionScore from float.

        Args:
            score: Float value between 0.0 and 1.0

        Returns:
            EmotionScore instance

        Raises:
            ValueError: If score is out of range
        """
        return cls(value=Decimal(str(round(score, 4))))

    def to_float(self) -> float:
        """Convert score to float.

        Returns:
            Float representation of score
        """
        return float(self.value)

    def to_percentage(self) -> int:
        """Convert score to percentage (0-100).

        Returns:
            Integer percentage
        """
        return int(self.value * 100)

    @property
    def is_high_confidence(self) -> bool:
        """Check if score indicates high confidence (>= 0.7)."""
        return self.value >= Decimal("0.7")

    @property
    def is_low_confidence(self) -> bool:
        """Check if score indicates low confidence (< 0.5)."""
        return self.value < Decimal("0.5")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.to_percentage()}%"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"EmotionScore(value={self.value})"
