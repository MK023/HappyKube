"""API authentication middleware."""

from fastapi import Header, HTTPException, status

from config import get_logger, settings

logger = get_logger(__name__)


async def require_api_key(x_api_key: str | None = Header(None)) -> None:
    """
    FastAPI dependency to require valid API key.

    Checks X-API-Key header against configured API keys.

    Args:
        x_api_key: API key from header

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key
    if not settings.api_keys or x_api_key not in settings.api_keys:
        logger.warning(
            "Invalid API key",
            key_prefix=x_api_key[:8] if x_api_key else "None",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("API key validated")
