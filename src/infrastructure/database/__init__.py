"""Database infrastructure layer."""

from typing import Generator

from sqlalchemy.orm import Session

from .connection import (
    close_database,
    get_db_session,
    get_engine,
    health_check,
    init_database,
)
from .encryption import FieldEncryption, get_encryption
from .models import APIKeyModel, AuditLogModel, Base, EmotionModel, UserModel


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session.

    Yields:
        SQLAlchemy Session with automatic commit/rollback

    Usage:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db session
    """
    with get_db_session() as session:
        yield session


__all__ = [
    # Models
    "Base",
    "UserModel",
    "EmotionModel",
    "APIKeyModel",
    "AuditLogModel",
    # Connection
    "get_engine",
    "get_db_session",
    "get_db",  # FastAPI dependency
    "init_database",
    "close_database",
    "health_check",
    # Encryption
    "FieldEncryption",
    "get_encryption",
]
