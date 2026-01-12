"""Initial schema creation with encrypted fields and indexes.

Revision ID: 001
Revises: None
Create Date: 2025-12-26 01:00:00

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema - Create all tables with proper indexes."""

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="Internal user UUID"),
        sa.Column(
            "telegram_id_hash",
            sa.String(length=64),
            nullable=False,
            comment="SHA-256 hash of Telegram user ID",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="User registration timestamp (UTC)",
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last interaction timestamp (UTC)",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether user account is active",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id_hash"),
        comment="Telegram bot users with hashed IDs for privacy",
    )
    op.create_index("ix_users_telegram_id_hash", "users", ["telegram_id_hash"], unique=False)

    # Create emotions table
    op.create_table(
        "emotions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="Emotion record UUID"),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Reference to users.id",
        ),
        sa.Column(
            "text_encrypted",
            sa.LargeBinary(),
            nullable=False,
            comment="User text encrypted with AES-256 (Fernet)",
        ),
        sa.Column(
            "emotion",
            sa.String(length=50),
            nullable=False,
            comment="Detected emotion (anger, joy, sadness, fear, etc.)",
        ),
        sa.Column("score", sa.Float(), nullable=False, comment="Confidence score (0.0 to 1.0)"),
        sa.Column(
            "model_type",
            sa.String(length=20),
            nullable=False,
            comment="ML model used (italian_emotion, english_emotion, sentiment)",
        ),
        sa.Column(
            "sentiment",
            sa.String(length=20),
            nullable=True,
            comment="Sentiment classification (positive, negative, neutral)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Analysis timestamp (UTC)",
        ),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional metadata (model version, confidence breakdown, etc.)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        comment="Emotion analysis records with encrypted user text",
    )
    op.create_index("ix_emotions_user_id", "emotions", ["user_id"], unique=False)
    op.create_index("ix_emotions_emotion", "emotions", ["emotion"], unique=False)
    op.create_index("ix_emotions_model_type", "emotions", ["model_type"], unique=False)
    op.create_index("ix_emotions_created_at", "emotions", ["created_at"], unique=False)
    # Composite index for common query pattern (user_id + created_at DESC)
    op.create_index(
        "ix_emotions_user_created", "emotions", ["user_id", sa.text("created_at DESC")], unique=False
    )

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="API key UUID"),
        sa.Column(
            "key_hash",
            sa.String(length=64),
            nullable=False,
            comment="Bcrypt hash of API key",
        ),
        sa.Column("name", sa.String(length=100), nullable=False, comment="API key name/description"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Whether API key is active",
        ),
        sa.Column(
            "rate_limit_per_minute",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
            comment="Rate limit for this API key (requests/minute)",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="API key creation timestamp (UTC)",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="API key expiration timestamp (UTC)",
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Last usage timestamp (UTC)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
        comment="API keys for authentication with bcrypt hashing",
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=False)

    # Create audit_log table
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="Audit log entry UUID"),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Reference to users.id (if authenticated)",
        ),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
            comment="Action performed (emotion_analysis, report_request, etc.)",
        ),
        sa.Column(
            "endpoint",
            sa.String(length=100),
            nullable=True,
            comment="API endpoint called",
        ),
        sa.Column(
            "ip_address",
            sa.String(length=45),  # IPv6 max length
            nullable=True,
            comment="Client IP address",
        ),
        sa.Column("user_agent", sa.Text(), nullable=True, comment="Client user agent"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Log entry timestamp (UTC)",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        comment="Audit log for security tracking and compliance",
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"], unique=False)
    op.create_index("ix_audit_log_action", "audit_log", ["action"], unique=False)
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade database schema - Drop all tables."""
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_table("api_keys")

    op.drop_index("ix_emotions_user_created", table_name="emotions")
    op.drop_index("ix_emotions_created_at", table_name="emotions")
    op.drop_index("ix_emotions_model_type", table_name="emotions")
    op.drop_index("ix_emotions_emotion", table_name="emotions")
    op.drop_index("ix_emotions_user_id", table_name="emotions")
    op.drop_table("emotions")

    op.drop_index("ix_users_telegram_id_hash", table_name="users")
    op.drop_table("users")
