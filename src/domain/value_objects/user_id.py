"""User ID value object."""

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class UserId:
    """Immutable value object representing a Telegram user ID.

    Attributes:
        telegram_id: Original Telegram user ID
        hashed_id: SHA-256 hash of telegram_id (for database storage)
    """

    telegram_id: str
    hashed_id: str

    def __post_init__(self) -> None:
        """Validate user ID."""
        # Skip validation if telegram_id is empty (used in from_hash for DB queries)
        if not self.telegram_id:
            if not self.hashed_id:
                raise ValueError("Either telegram_id or hashed_id must be provided")
            return

        if not self.telegram_id.isdigit():
            raise ValueError(f"Telegram ID must be numeric, got: {self.telegram_id}")

        # Verify or compute hashed_id
        expected_hash = self._compute_hash(self.telegram_id)
        if self.hashed_id and self.hashed_id != expected_hash:
            raise ValueError("Provided hashed_id does not match telegram_id")

        if not self.hashed_id:
            object.__setattr__(self, "hashed_id", expected_hash)

    @staticmethod
    def _compute_hash(telegram_id: str) -> str:
        """Compute SHA-256 hash of telegram_id.

        Args:
            telegram_id: Telegram user ID

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(telegram_id.encode()).hexdigest()

    @classmethod
    def from_telegram(cls, telegram_id: str | int) -> "UserId":
        """Create UserId from Telegram ID.

        Args:
            telegram_id: Telegram user ID (int or string)

        Returns:
            UserId instance
        """
        telegram_id_str = str(telegram_id)
        hashed = cls._compute_hash(telegram_id_str)
        return cls(telegram_id=telegram_id_str, hashed_id=hashed)

    @classmethod
    def from_hash(cls, hashed_id: str) -> "UserId":
        """Create UserId from existing hash (used when loading from DB).

        Note: This creates a partial UserId without the original telegram_id.

        Args:
            hashed_id: SHA-256 hash

        Returns:
            UserId instance with empty telegram_id
        """
        # For DB queries where we only have the hash
        return cls(telegram_id="", hashed_id=hashed_id)

    def __str__(self) -> str:
        """String representation (shows hash, not original ID for privacy)."""
        return f"User({self.hashed_id[:8]}...)"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"UserId(telegram_id={'***' if self.telegram_id else 'N/A'}, hashed_id={self.hashed_id[:16]}...)"
