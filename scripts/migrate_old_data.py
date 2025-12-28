#!/usr/bin/env python3
"""
Migration script to transfer data from old HappyKube schema to new v2 schema.

This script:
1. Reads data from old 'emotions' table (plaintext)
2. Encrypts user text with Fernet
3. Creates users with hashed telegram_ids
4. Inserts into new schema with proper foreign keys

Run with: python scripts/migrate_old_data.py
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.config import get_logger, settings
from src.infrastructure.database.encryption import get_encryption
from src.infrastructure.database.models import EmotionModel, UserModel

logger = get_logger(__name__)


def hash_telegram_id(telegram_id: str) -> str:
    """Hash telegram ID with SHA-256."""
    return hashlib.sha256(telegram_id.encode()).hexdigest()


def migrate_data() -> None:
    """Migrate data from old schema to new schema."""
    logger.info("Starting data migration from old HappyKube schema")

    # Connect to database
    engine = create_engine(settings.database_url)
    encryption = get_encryption()

    with Session(engine) as session:
        # Check if old emotions table exists
        result = session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'emotions_old'
                )
            """
            )
        )
        old_table_exists = result.scalar()

        if not old_table_exists:
            logger.warning(
                "Old 'emotions_old' table not found. "
                "Please rename your old 'emotions' table to 'emotions_old' first."
            )
            logger.info(
                "Run: ALTER TABLE emotions RENAME TO emotions_old; "
                "(only if you have old data to migrate)"
            )
            return

        # Fetch all old emotion records
        logger.info("Fetching old emotion records")
        old_records = session.execute(
            text(
                """
                SELECT user_id, date, text, emotion, score, model_type
                FROM emotions_old
                ORDER BY date ASC
            """
            )
        ).fetchall()

        logger.info(f"Found {len(old_records)} old records to migrate")

        if len(old_records) == 0:
            logger.info("No records to migrate")
            return

        # Track user_id -> UUID mapping
        user_map: dict[str, uuid4] = {}  # type: ignore
        migrated_count = 0
        error_count = 0

        for record in old_records:
            try:
                user_id_str = str(record.user_id)
                telegram_hash = hash_telegram_id(user_id_str)

                # Get or create user
                if user_id_str not in user_map:
                    # Check if user already exists
                    existing_user = (
                        session.query(UserModel)
                        .filter_by(telegram_id_hash=telegram_hash)
                        .first()
                    )

                    if existing_user:
                        user_uuid = existing_user.id
                    else:
                        # Create new user
                        user_uuid = uuid4()
                        new_user = UserModel(
                            id=user_uuid,
                            telegram_id_hash=telegram_hash,
                            created_at=record.date or datetime.utcnow(),
                            last_seen_at=record.date,
                            is_active=True,
                        )
                        session.add(new_user)

                    user_map[user_id_str] = user_uuid
                else:
                    user_uuid = user_map[user_id_str]

                # Encrypt text
                text_encrypted = encryption.encrypt(record.text or "")

                # Create emotion record
                emotion = EmotionModel(
                    id=uuid4(),
                    user_id=user_uuid,
                    text_encrypted=text_encrypted,
                    emotion=record.emotion or "unknown",
                    score=float(record.score or 0.0),
                    model_type=record.model_type or "italian_emotion",
                    sentiment=None,  # Old schema didn't have sentiment
                    created_at=record.date or datetime.utcnow(),
                    metadata={"migrated_from": "v1", "migration_date": datetime.utcnow().isoformat()},
                )
                session.add(emotion)

                migrated_count += 1

                # Commit every 100 records
                if migrated_count % 100 == 0:
                    session.commit()
                    logger.info(f"Migrated {migrated_count} records so far...")

            except Exception as e:
                error_count += 1
                logger.error(f"Error migrating record: {e}", record=str(record))
                session.rollback()
                continue

        # Final commit
        session.commit()

        logger.info(
            f"Migration completed: {migrated_count} records migrated, {error_count} errors"
        )
        logger.info(f"Created {len(user_map)} users")

        # Optionally rename old table to archive
        logger.info("You can now archive the old table with:")
        logger.info("  ALTER TABLE emotions_old RENAME TO emotions_archive;")


if __name__ == "__main__":
    try:
        migrate_data()
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
