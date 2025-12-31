"""API Key repository for database operations."""

import bcrypt
from datetime import datetime
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from uuid import UUID

from config import get_logger
from infrastructure.database.models import APIKeyModel

logger = get_logger(__name__)


class APIKeyRepository:
    """
    Repository for API key database operations.

    Handles secure API key storage with bcrypt hashing.
    """

    def __init__(self, engine: Engine) -> None:
        """
        Initialize API key repository.

        Args:
            engine: SQLAlchemy engine
        """
        self.engine = engine

    def validate_key(self, api_key: str) -> tuple[bool, UUID | None, int | None]:
        """
        Validate API key against database.

        Args:
            api_key: Plaintext API key from request

        Returns:
            Tuple of (is_valid, api_key_id, rate_limit_per_minute)
        """
        with Session(self.engine) as session:
            # Get all active API keys
            stmt = select(APIKeyModel).where(
                APIKeyModel.is_active == True  # noqa: E712
            )
            api_keys = session.scalars(stmt).all()

            # Check each key using constant-time bcrypt comparison
            for key_model in api_keys:
                try:
                    # Check expiration
                    if key_model.expires_at and key_model.expires_at < datetime.now():
                        logger.debug("API key expired", key_id=str(key_model.id))
                        continue

                    # Verify using bcrypt (constant-time comparison)
                    if bcrypt.checkpw(api_key.encode(), key_model.key_hash.encode()):
                        # Update last_used_at timestamp
                        key_model.last_used_at = datetime.now()
                        session.commit()

                        logger.info(
                            "API key validated",
                            key_id=str(key_model.id),
                            key_name=key_model.name
                        )

                        return True, key_model.id, key_model.rate_limit_per_minute

                except Exception as e:
                    logger.error(
                        "Error validating API key",
                        key_id=str(key_model.id),
                        error=str(e)
                    )
                    continue

            logger.warning("Invalid API key attempt", key_prefix=api_key[:8])
            return False, None, None

    def create_key(
        self,
        api_key: str,
        name: str,
        rate_limit_per_minute: int = 100,
        expires_at: datetime | None = None
    ) -> APIKeyModel:
        """
        Create new API key in database.

        Args:
            api_key: Plaintext API key to hash and store
            name: Human-readable name/description
            rate_limit_per_minute: Rate limit for this key
            expires_at: Optional expiration timestamp

        Returns:
            Created APIKeyModel instance
        """
        with Session(self.engine) as session:
            # Hash the key with bcrypt (with salt)
            key_hash = bcrypt.hashpw(api_key.encode(), bcrypt.gensalt()).decode()

            # Create model
            model = APIKeyModel(
                key_hash=key_hash,
                name=name,
                is_active=True,
                rate_limit_per_minute=rate_limit_per_minute,
                expires_at=expires_at
            )

            session.add(model)
            session.commit()
            session.refresh(model)

            logger.info(
                "API key created",
                key_id=str(model.id),
                key_name=name,
                rate_limit=rate_limit_per_minute
            )

            return model

    def deactivate_key(self, key_id: UUID) -> bool:
        """
        Deactivate an API key.

        Args:
            key_id: UUID of key to deactivate

        Returns:
            True if deactivated, False if not found
        """
        with Session(self.engine) as session:
            stmt = select(APIKeyModel).where(APIKeyModel.id == key_id)
            model = session.scalar(stmt)

            if not model:
                logger.warning("API key not found for deactivation", key_id=str(key_id))
                return False

            model.is_active = False
            session.commit()

            logger.info("API key deactivated", key_id=str(key_id), key_name=model.name)
            return True

    def list_keys(self, include_inactive: bool = False) -> list[APIKeyModel]:
        """
        List all API keys.

        Args:
            include_inactive: Whether to include inactive keys

        Returns:
            List of APIKeyModel instances
        """
        with Session(self.engine) as session:
            stmt = select(APIKeyModel)

            if not include_inactive:
                stmt = stmt.where(APIKeyModel.is_active == True)  # noqa: E712

            models = session.scalars(stmt).all()
            return list(models)
