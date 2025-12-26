"""User repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...application.interfaces.user_repository import IUserRepository
from ...config import get_logger
from ...domain import User, UserId
from ..database import UserModel

logger = get_logger(__name__)


class UserRepository(IUserRepository):
    """Repository for user persistence."""

    def __init__(self, session: Session) -> None:
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def save(self, user: User) -> User:
        """
        Save or update user.

        Args:
            user: User entity

        Returns:
            Saved User
        """
        db_user = UserModel(
            id=user.id,
            telegram_id_hash=user.user_id.hashed_id,
            created_at=user.created_at,
            last_seen_at=user.last_seen_at,
            is_active=user.is_active,
        )

        self.session.merge(db_user)  # Use merge for update or insert
        logger.info("User saved", user_id=str(user.id), hash=user.user_id.hashed_id[:8])
        return user

    def find_by_id(self, user_id: UUID) -> User | None:
        """Find user by UUID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        db_user = self.session.scalars(stmt).first()

        if db_user is None:
            return None

        return self._to_domain(db_user)

    def find_by_telegram_hash(self, telegram_hash: str) -> User | None:
        """Find user by telegram ID hash."""
        stmt = select(UserModel).where(UserModel.telegram_id_hash == telegram_hash)
        db_user = self.session.scalars(stmt).first()

        if db_user is None:
            return None

        return self._to_domain(db_user)

    def find_or_create_by_telegram_id(self, telegram_id: str) -> User:
        """
        Find existing user or create new one.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User entity (existing or new)
        """
        user_id_vo = UserId.from_telegram(telegram_id)
        existing = self.find_by_telegram_hash(user_id_vo.hashed_id)

        if existing:
            # Update last seen
            existing.update_last_seen()
            self.save(existing)
            logger.debug("Existing user found", user_id=str(existing.id))
            return existing

        # Create new user
        new_user = User.create(telegram_id)
        self.save(new_user)
        logger.info("New user created", user_id=str(new_user.id))
        return new_user

    def _to_domain(self, db_user: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=db_user.id,
            user_id=UserId.from_hash(db_user.telegram_id_hash),
            created_at=db_user.created_at,
            last_seen_at=db_user.last_seen_at,
            is_active=db_user.is_active,
        )
