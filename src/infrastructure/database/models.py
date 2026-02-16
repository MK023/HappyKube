"""SQLAlchemy 2.0 database models with encryption support."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Enable type checking for mapped columns
    type_annotation_map = {
        dict[str, Any]: JSONB,
    }


class UserModel(Base):
    """
    User table model.

    Stores Telegram bot users with hashed IDs for privacy.
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="Internal user UUID"
    )

    # Telegram ID (hashed with SHA-256 for privacy)
    telegram_id_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of Telegram user ID",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="User registration timestamp (UTC)",
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last interaction timestamp (UTC)"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether user account is active"
    )

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<UserModel(id={self.id}, hash={self.telegram_id_hash[:8]}..., active={self.is_active})>"


class EmotionModel(Base):
    """
    Emotion analysis records table.

    Stores emotion/sentiment analysis results with encrypted user text.
    Partitioned by created_at for performance (manual setup required).
    """

    __tablename__ = "emotions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="Emotion record UUID"
    )

    # Foreign key to users table
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True, comment="Reference to users.id"
    )

    # Encrypted user text (PII - AES-256 encrypted)
    text_encrypted: Mapped[bytes] = mapped_column(
        LargeBinary, nullable=False, comment="User text encrypted with AES-256 (Fernet)"
    )

    # Analysis results
    emotion: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Detected emotion (anger, joy, sadness, fear, etc.)",
    )

    score: Mapped[float] = mapped_column(nullable=False, comment="Confidence score (0.0 to 1.0)")

    # Model information
    model_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="ML model used (italian_emotion, english_emotion, sentiment)",
    )

    # Optional sentiment (for dual analysis)
    sentiment: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Sentiment classification (positive, negative, neutral)"
    )

    # Timestamp (used for partitioning)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Analysis timestamp (UTC)",
    )

    # Additional metadata (model version, etc.)
    extra_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata (model version, confidence breakdown, etc.)",
    )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"<EmotionModel(id={self.id}, user_id={self.user_id}, "
            f"emotion={self.emotion}, score={self.score:.2f}, model={self.model_type})>"
        )


class APIKeyModel(Base):
    """
    API keys table for authentication.

    Stores bcrypt-hashed API keys for securing endpoints.
    """

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="API key UUID"
    )

    # Bcrypt-hashed API key (never store plaintext!)
    key_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, comment="Bcrypt hash of API key"
    )

    # Metadata
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="API key name/description"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether API key is active"
    )

    # Rate limiting (requests per minute)
    rate_limit_per_minute: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="Rate limit for this API key (requests/minute)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="API key creation timestamp (UTC)",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="API key expiration timestamp (UTC)"
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last usage timestamp (UTC)"
    )

    def __repr__(self) -> str:
        """Developer representation."""
        return f"<APIKeyModel(id={self.id}, name={self.name}, active={self.is_active})>"


class AuditLogModel(Base):
    """
    Audit log table for security tracking.

    Records all API access for forensics and compliance.
    """

    __tablename__ = "audit_log"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, comment="Audit log entry UUID"
    )

    # User reference (nullable for unauthenticated requests)
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Reference to users.id (if authenticated)",
    )

    # Action details
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action performed (emotion_analysis, report_request, etc.)",
    )

    endpoint: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="API endpoint called"
    )

    # Request metadata
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="Client IP address"  # IPv6 max length
    )

    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True, comment="Client user agent")

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Log entry timestamp (UTC)",
    )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"<AuditLogModel(id={self.id}, action={self.action}, "
            f"user_id={self.user_id}, ip={self.ip_address})>"
        )
