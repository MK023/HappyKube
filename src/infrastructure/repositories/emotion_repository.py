"""Emotion repository implementation with SQLAlchemy."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from application.interfaces.emotion_repository import IEmotionRepository
from config import get_logger
from domain import EmotionRecord, EmotionScore, EmotionType, ModelType, SentimentType

from ..database import EmotionModel, get_encryption

logger = get_logger(__name__)


class EmotionRepository(IEmotionRepository):
    """
    Repository for emotion persistence with encryption.

    Handles conversion between domain entities and database models.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self.encryption = get_encryption()

    def save(self, emotion: EmotionRecord) -> EmotionRecord:
        """
        Save emotion record to database.

        Args:
            emotion: EmotionRecord entity

        Returns:
            Saved EmotionRecord with ID
        """
        # Convert domain entity to database model
        db_emotion = EmotionModel(
            id=emotion.id,
            user_id=emotion.user_id,
            text_encrypted=self.encryption.encrypt(emotion.text),
            emotion=emotion.emotion.value,
            score=emotion.score.to_float(),
            model_type=emotion.model_type.value,
            sentiment=emotion.sentiment.value if emotion.sentiment else None,
            created_at=emotion.created_at,
            metadata=emotion.metadata,
        )

        self.session.add(db_emotion)
        self.session.flush()  # Ensure ID is generated

        logger.info(
            "Emotion saved",
            emotion_id=str(emotion.id),
            user_id=str(emotion.user_id),
            emotion=emotion.emotion.value,
        )

        return emotion

    def find_by_id(self, emotion_id: UUID) -> EmotionRecord | None:
        """
        Find emotion by ID.

        Args:
            emotion_id: Emotion UUID

        Returns:
            EmotionRecord or None
        """
        stmt = select(EmotionModel).where(EmotionModel.id == emotion_id)
        db_emotion = self.session.scalars(stmt).first()

        if db_emotion is None:
            return None

        return self._to_domain(db_emotion)

    def find_by_user(
        self,
        user_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EmotionRecord]:
        """
        Find emotions for user with pagination.

        Args:
            user_id: User UUID
            limit: Maximum results
            offset: Result offset

        Returns:
            List of EmotionRecord
        """
        stmt = (
            select(EmotionModel)
            .where(EmotionModel.user_id == user_id)
            .order_by(EmotionModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        db_emotions = self.session.scalars(stmt).all()
        return [self._to_domain(e) for e in db_emotions]

    def find_by_user_and_period(
        self,
        user_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[EmotionRecord]:
        """
        Find emotions for user within date range.

        Args:
            user_id: User UUID
            start_date: Start of period
            end_date: End of period

        Returns:
            List of EmotionRecord
        """
        stmt = (
            select(EmotionModel)
            .where(
                and_(
                    EmotionModel.user_id == user_id,
                    EmotionModel.created_at >= start_date,
                    EmotionModel.created_at <= end_date,
                )
            )
            .order_by(EmotionModel.created_at.desc())
        )

        db_emotions = self.session.scalars(stmt).all()
        return [self._to_domain(e) for e in db_emotions]

    def _to_domain(self, db_emotion: EmotionModel) -> EmotionRecord:
        """
        Convert database model to domain entity.

        Args:
            db_emotion: EmotionModel from database

        Returns:
            EmotionRecord domain entity
        """
        # Decrypt text
        decrypted_text = self.encryption.decrypt(db_emotion.text_encrypted)

        # Convert to domain entity
        return EmotionRecord(
            id=db_emotion.id,
            user_id=db_emotion.user_id,
            text=decrypted_text,
            emotion=EmotionType.from_label(db_emotion.emotion),
            sentiment=(
                SentimentType.from_label(db_emotion.sentiment) if db_emotion.sentiment else None
            ),
            score=EmotionScore.from_float(db_emotion.score),
            model_type=ModelType(db_emotion.model_type),
            created_at=db_emotion.created_at,
            metadata=db_emotion.metadata or {},
        )
