"""User domain entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..value_objects.user_id import UserId


@dataclass
class User:
    """User entity representing a Telegram bot user.

    Attributes:
        id: Internal UUID (primary key)
        user_id: Telegram user ID value object
        created_at: User registration timestamp
        last_seen_at: Last interaction timestamp
        is_active: Whether user is active
    """

    id: UUID
    user_id: UserId
    created_at: datetime
    last_seen_at: datetime | None = None
    is_active: bool = True

    @classmethod
    def create(cls, telegram_id: str | int) -> "User":
        """Factory method to create a new user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            New User instance
        """
        return cls(
            id=uuid4(),
            user_id=UserId.from_telegram(telegram_id),
            created_at=datetime.now(timezone.utc),
            last_seen_at=None,
            is_active=True,
        )

    def update_last_seen(self) -> None:
        """Update last_seen_at timestamp."""
        self.last_seen_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"User(id={self.id}, user_id={self.user_id}, "
            f"is_active={self.is_active}, created_at={self.created_at})"
        )
