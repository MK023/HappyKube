"""Monthly report routes."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from application.dto.emotion_dto import MonthlyStatisticsResponse
from application.services.emotion_service import EmotionService
from config import get_logger
from infrastructure.cache import get_cache
from infrastructure.database import get_db
from infrastructure.ml import ModelFactory
from infrastructure.repositories import EmotionRepository, UserRepository

logger = get_logger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


def _get_emotion_service(db: Session) -> EmotionService:
    """Create EmotionService instance with dependencies."""
    cache = get_cache()
    model_factory = ModelFactory()

    emotion_repo = EmotionRepository(db)
    user_repo = UserRepository(db)

    return EmotionService(
        emotion_repo=emotion_repo,
        user_repo=user_repo,
        model_factory=model_factory,
        cache=cache,
    )


@router.get(
    "/monthly/{telegram_id}/{month}",
    response_model=MonthlyStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get monthly emotion statistics",
    description="""
    Get comprehensive monthly emotion statistics for a user.

    **Features:**
    - Emotion breakdown with counts, percentages, and average scores
    - Sentiment distribution (positive/negative/neutral)
    - Active days tracking
    - Dominant emotion identification
    - Auto-generated insights in Italian

    **Month format:** YYYY-MM (e.g., 2026-01 for January 2026)

    **Example response:**
    ```json
    {
      "user_id": "abc123...",
      "period": "2026-01",
      "total_messages": 87,
      "active_days": 28,
      "emotions": {
        "joy": {"count": 35, "percentage": 40.2, "avg_score": 0.89}
      },
      "sentiment": {"positive": 62.5, "negative": 20.1, "neutral": 17.4},
      "dominant_emotion": "joy",
      "insights": [
        {
          "type": "positive_month",
          "message": "🎉 Gennaio è stato un mese positivo! (62% emozioni positive)",
          "icon": "🎉"
        }
      ]
    }
    ```

    **Rate limit:** 30 requests per minute per user

    **Errors:**
    - 400: Invalid month format
    - 404: No data found for specified month
    - 429: Rate limit exceeded
    """,
    responses={
        200: {
            "description": "Monthly statistics successfully retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "abc123...",
                        "period": "2026-01",
                        "total_messages": 87,
                        "active_days": 28,
                        "emotions": {
                            "joy": {"count": 35, "percentage": 40.2, "avg_score": 0.89},
                            "sadness": {"count": 12, "percentage": 13.8, "avg_score": 0.82}
                        },
                        "sentiment": {"positive": 62.5, "negative": 20.1, "neutral": 17.4},
                        "dominant_emotion": "joy",
                        "insights": [
                            {
                                "type": "positive_month",
                                "message": "🎉 Gennaio è stato un mese positivo!",
                                "icon": "🎉"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Invalid month format (use YYYY-MM)"},
        404: {"description": "No emotion data found for the specified month"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit("30/minute")
async def get_monthly_report(
    request: Request,
    telegram_id: str,
    month: str,
    db: Session = Depends(get_db)
) -> MonthlyStatisticsResponse:
    """
    Get monthly emotion statistics.

    Args:
        request: FastAPI request object (for rate limiting)
        telegram_id: Telegram user ID
        month: Month in YYYY-MM format
        db: Database session (injected by FastAPI)

    Returns:
        MonthlyStatisticsResponse with complete statistics

    Raises:
        HTTPException: If month format is invalid or no data found
    """
    try:
        service = _get_emotion_service(db)
        stats = service.get_monthly_statistics(telegram_id, month)

        logger.info(
            "Monthly report generated",
            telegram_id=telegram_id,
            month=month,
            total_messages=stats.total_messages
        )

        return stats

    except ValueError as e:
        error_msg = str(e)
        if "Invalid month format" in error_msg:
            logger.warning("Invalid month format", telegram_id=telegram_id, month=month)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            ) from e
        elif "No emotion data" in error_msg:
            logger.info("No data for month", telegram_id=telegram_id, month=month)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            ) from e
        else:
            logger.error("Unexpected error", telegram_id=telegram_id, month=month, error=error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            ) from e

    except Exception as e:
        logger.error(
            "Failed to generate monthly report",
            telegram_id=telegram_id,
            month=month,
            error=str(e),
            exc_info=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate monthly report"
        ) from e
