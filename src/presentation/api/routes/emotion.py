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


@router.post(
    "/emotion",
    response_model=EmotionAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze emotion and sentiment from text",
    description="""
    Analyze emotion and sentiment from user text using Groq (Llama 3.3 70B).

    **Authentication:** Requires API key (X-API-Key header)

    **Features:**
    - Emotion detection (joy, sadness, anger, fear, love, surprise)
    - Sentiment analysis (positive, negative, neutral)
    - Confidence scores (0.0 - 1.0)
    - Automatic storage in database for reporting
    - Results cached for 1 hour

    **Rate limit:** 100 requests per minute

    **Errors:**
    - 400: Invalid text or user_id
    - 401: Missing or invalid API key
    - 429: Rate limit exceeded
    - 500: ML model error
    """,
    responses={
        200: {
            "description": "Emotion analysis successful",
            "content": {
                "application/json": {
                    "example": {
                        "emotion": "joy",
                        "sentiment": "positive",
                        "score": 0.92,
                        "message": "Emotion detected successfully"
                    }
                }
            }
        },
        400: {"description": "Invalid input (empty text or invalid user_id)"},
        401: {"description": "Missing or invalid API key"},
        429: {"description": "Rate limit exceeded (100/min)"},
        500: {"description": "ML model error or internal server error"}
    }
)
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


@router.get(
    "/report",
    response_model=EmotionReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user emotion history report",
    description="""
    Retrieve emotion history for a specific user with optional month filter.

    **Authentication:** Requires API key (X-API-Key header)

    **Query Parameters:**
    - user_id (required): Telegram user ID
    - month (optional): Filter by month in YYYY-MM format (e.g., 2026-01)

    **Features:**
    - Complete emotion history
    - Optional monthly filtering
    - Sorted by date (most recent first)
    - Includes emotion type, sentiment, score, timestamp

    **Rate limit:** 50 requests per minute

    **Errors:**
    - 400: Invalid user_id or month format
    - 401: Missing or invalid API key
    - 404: User not found
    - 429: Rate limit exceeded
    """,
    responses={
        200: {
            "description": "Report retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "123456789",
                        "total_records": 42,
                        "emotions": [
                            {
                                "emotion": "joy",
                                "sentiment": "positive",
                                "score": 0.89,
                                "timestamp": "2026-01-15T14:30:00Z"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid user_id or month format"},
        401: {"description": "Missing or invalid API key"},
        404: {"description": "User not found"},
        429: {"description": "Rate limit exceeded (50/min)"}
    }
)
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
