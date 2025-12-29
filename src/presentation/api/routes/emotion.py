"""Emotion analysis API routes."""

from flask import Blueprint, jsonify, request

from application.dto.emotion_dto import EmotionAnalysisRequest
from application.services import EmotionService
from config import get_logger
from infrastructure.cache import get_cache
from infrastructure.database import get_db_session
from infrastructure.ml import get_model_factory
from infrastructure.repositories import EmotionRepository, UserRepository
from ..middleware import rate_limit, require_api_key

logger = get_logger(__name__)

# Create blueprint
emotion_bp = Blueprint("emotion", __name__, url_prefix="/api/v1")


@emotion_bp.route("/emotion", methods=["POST"])
@require_api_key
@rate_limit(max_requests=100, window_seconds=60)
def analyze_emotion():
    """
    Analyze emotion from text.

    Request Body:
        {
            "user_id": "123456789",
            "text": "I feel happy today!"
        }

    Returns:
        EmotionAnalysisResponse JSON
    """
    try:
        # Validate request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        emotion_request = EmotionAnalysisRequest(**data)

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

            # Analyze emotion
            response = service.analyze_emotion(
                telegram_id=emotion_request.user_id,
                text=emotion_request.text,
            )

        logger.info(
            "Emotion analyzed via API",
            user_id=emotion_request.user_id,
            emotion=response.emotion,
        )

        return jsonify(response.model_dump()), 200

    except ValueError as e:
        logger.warning("Validation error", error=str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error("Emotion analysis error", error=str(e))
        return jsonify({"error": "Internal server error"}), 500


@emotion_bp.route("/report", methods=["GET"])
@require_api_key
@rate_limit(max_requests=50, window_seconds=60)
def get_report():
    """
    Get emotion report for user.

    Query Parameters:
        user_id (required): Telegram user ID
        month (optional): Filter by month (YYYY-MM)

    Returns:
        EmotionReportResponse JSON
    """
    try:
        # Get query parameters
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id parameter"}), 400

        month = request.args.get("month")

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

        return jsonify(response.model_dump()), 200

    except Exception as e:
        logger.error("Report generation error", error=str(e))
        return jsonify({"error": "Internal server error"}), 500
