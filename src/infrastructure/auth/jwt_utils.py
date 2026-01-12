"""JWT token utilities for authentication and audit logging."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


class JWTUtils:
    """
    Utility class for JWT token operations.

    Handles encoding, decoding, and validation of JWT tokens.
    """

    @staticmethod
    def create_token(
        user_id: UUID,
        telegram_id: str,
        expires_in_hours: int = 24
    ) -> str:
        """
        Create a new JWT token for a user.

        Args:
            user_id: Internal user UUID
            telegram_id: Telegram user ID
            expires_in_hours: Token expiration time in hours

        Returns:
            Encoded JWT token string
        """
        payload = {
            "user_id": str(user_id),
            "telegram_id": telegram_id,
            "iat": datetime.now(UTC),
            "exp": datetime.now(UTC) + timedelta(hours=expires_in_hours)
        }

        token = jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm="HS256"
        )

        logger.debug("JWT token created", user_id=str(user_id), expires_in=expires_in_hours)
        return token

    @staticmethod
    def decode_token(token: str) -> dict | None:
        """
        Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=["HS256"]
            )

            logger.debug("JWT token decoded", user_id=payload.get("user_id"))
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired", token_prefix=token[:20])
            return None

        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e), token_prefix=token[:20])
            return None

        except Exception as e:
            logger.error("Error decoding JWT token", error=str(e), exc_info=e)
            return None

    @staticmethod
    def extract_user_id_from_token(token: str) -> UUID | None:
        """
        Extract user_id from JWT token.

        Args:
            token: JWT token string

        Returns:
            User UUID or None if invalid
        """
        payload = JWTUtils.decode_token(token)

        if not payload:
            return None

        try:
            user_id_str = payload.get("user_id")
            if user_id_str:
                return UUID(user_id_str)
        except (ValueError, TypeError) as e:
            logger.error("Invalid user_id in JWT payload", error=str(e))

        return None

    @staticmethod
    def extract_from_request_header(authorization_header: str | None) -> UUID | None:
        """
        Extract user_id from Authorization header.

        Supports formats:
        - Bearer <token>
        - JWT <token>
        - <token>

        Args:
            authorization_header: Value of Authorization header

        Returns:
            User UUID or None if invalid/missing
        """
        if not authorization_header:
            return None

        # Remove "Bearer " or "JWT " prefix if present
        token = authorization_header
        if " " in token:
            prefix, token = token.split(" ", 1)
            if prefix.upper() not in ("BEARER", "JWT"):
                logger.warning("Invalid authorization scheme", prefix=prefix)
                return None

        return JWTUtils.extract_user_id_from_token(token)
