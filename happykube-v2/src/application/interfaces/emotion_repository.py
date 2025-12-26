"""Emotion repository interface (dependency inversion)."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from ...domain import EmotionRecord


class IEmotionRepository(ABC):
    """Interface for emotion data persistence."""

    @abstractmethod
    def save(self, emotion: EmotionRecord) -> EmotionRecord:
        """Save emotion record."""
        pass

    @abstractmethod
    def find_by_id(self, emotion_id: UUID) -> EmotionRecord | None:
        """Find emotion by ID."""
        pass

    @abstractmethod
    def find_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EmotionRecord]:
        """Find emotions for user."""
        pass

    @abstractmethod
    def find_by_user_and_period(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[EmotionRecord]:
        """Find emotions for user within date range."""
        pass
