"""User repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from domain import User


class IUserRepository(ABC):
    """Interface for user data persistence."""

    @abstractmethod
    def save(self, user: User) -> User:
        """Save or update user."""
        pass

    @abstractmethod
    def find_by_id(self, user_id: UUID) -> User | None:
        """Find user by internal UUID."""
        pass

    @abstractmethod
    def find_by_telegram_hash(self, telegram_hash: str) -> User | None:
        """Find user by hashed telegram ID."""
        pass

    @abstractmethod
    def find_or_create_by_telegram_id(self, telegram_id: str) -> User:
        """Find existing user or create new one."""
        pass
