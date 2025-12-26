"""Application interfaces (dependency inversion)."""

from .emotion_repository import IEmotionRepository
from .user_repository import IUserRepository

__all__ = [
    "IEmotionRepository",
    "IUserRepository",
]
