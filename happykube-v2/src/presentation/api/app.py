"""Flask application factory."""

from flask import Flask
from flask_cors import CORS

from ...config import get_logger, settings, setup_logging
from .routes import emotion_bp, health_bp

logger = get_logger(__name__)


def create_app() -> Flask:
    """
    Create and configure Flask application.

    Returns:
        Configured Flask app
    """
    # Setup logging first
    setup_logging()

    app = Flask(__name__)

    # Configure CORS
    if settings.cors_enabled:
        CORS(
            app,
            resources={r"/api/*": {"origins": settings.cors_origins}},
            allow_headers=["Content-Type", "X-API-Key"],
            methods=["GET", "POST", "OPTIONS"],
        )
        logger.info("CORS enabled", origins=settings.cors_origins)

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(emotion_bp)

    logger.info(
        "Flask app created",
        env=settings.app_env,
        debug=settings.debug,
        version=settings.app_version,
    )

    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {"error": "Not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error("Internal server error", error=str(error))
        return {"error": "Internal server error"}, 500

    return app


if __name__ == "__main__":
    # For local development only
    app = create_app()
    app.run(
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.debug,
    )
