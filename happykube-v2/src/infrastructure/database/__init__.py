"""Database infrastructure layer."""

from .connection import (
    close_database,
    get_db_session,
    get_engine,
    health_check,
    init_database,
)
from .encryption import FieldEncryption, get_encryption
from .models import APIKeyModel, AuditLogModel, Base, EmotionModel, UserModel

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
    "init_database",
    "close_database",
    "health_check",
    # Encryption
    "FieldEncryption",
    "get_encryption",
]
