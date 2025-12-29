"""Emotion analysis API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from application.dto.emotion_dto import (
    EmotionAnalysisRequest,
    EmotionAnalysisResponse,
    EmotionReportResponse,
)
from application.services import EmotionService
from config import get_logger
from infrastructure.cache import get_cache
from infrastructure.database import get_db_session
from infrastructure.ml import get_model_factory
from infrastructure.repositories import EmotionRepository, UserRepository
from ..middleware.auth import require_api_key

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["emotion"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/emotion", response_model=EmotionAnalysisResponse)
@limiter.limit("100/minute")
async def analyze_emotion(
    request: Request,
    emotion_request: EmotionAnalysisRequest,
    _: None = Depends(require_api_key),
):
    """
    Analyze emotion from text.

    Requires API key authentication.
    Rate limited to 100 requests per minute.
    """
    try:
        # Create service with dependencies
        with get_db_session() as session:
            emotion_repo = EmotionRepository(session)
            user_repo = UserRepository(session)
            service = EmotionService(
                emotion_repo=emotion_repo,
                user_repo=user_repo,
                model_factory=get_model_factory(),
                cache=get_cache(),
            )

            # Analyze emotion (async)
            response = await service.analyze_emotion(
                telegram_id=emotion_request.user_id,
                text=emotion_request.text,
            )

        logger.info(
            "Emotion analyzed via API",
            user_id=emotion_request.user_id,
            emotion=response.emotion,
        )

        return response

    except ValueError as e:
        logger.warning("Validation error", error=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Emotion analysis error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/report", response_model=EmotionReportResponse)
@limiter.limit("50/minute")
async def get_report(
    request: Request,
    user_id: str,
    month: str | None = None,
    _: None = Depends(require_api_key),
):
    """
    Get emotion report for user.

    Query Parameters:
        user_id (required): Telegram user ID
        month (optional): Filter by month (YYYY-MM)

    Requires API key authentication.
    Rate limited to 50 requests per minute.
    """
    try:
        # Create service
        with get_db_session() as session:
            emotion_repo = EmotionRepository(session)
            user_repo = UserRepository(session)
            service = EmotionService(
                emotion_repo=emotion_repo,
                user_repo=user_repo,
                model_factory=get_model_factory(),
                cache=get_cache(),
            )

            # Get report
            response = service.get_user_report(
                telegram_id=user_id,
                month=month,
            )

        logger.info("Report generated via API", user_id=user_id, records=response.total_records)

        return response

    except Exception as e:
        logger.error("Report generation error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
