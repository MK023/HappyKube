"""
Telegram Bot Webhook Handler - HappyKube 3.0

SECURITY FEATURES:
- Secret token validation (X-Telegram-Bot-Api-Secret-Token header)
- Request size limiting (handled by SlowAPI middleware)
- Rate limiting (10 requests per second per user)
- Payload structure validation
- HTTPS required (Fly.io provides TLS)
"""

from fastapi import APIRouter, Header, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from telegram import Bot, Update

from config import get_logger, get_settings
from presentation.bot.handlers import CommandHandlers, MessageHandlers

logger = get_logger(__name__)
settings = get_settings()

# Rate limiter for webhook endpoint
limiter = Limiter(key_func=get_remote_address)

# Create API router
router = APIRouter(prefix="/telegram", tags=["telegram"])

# Initialize bot handlers
messages = {
    "welcome": "Ciao! 😊 Sono HappyKube! Dimmi come ti senti oggi!",
    "ask_emotion": "Dimmi come ti senti, sono qui per ascoltarti!",
    "thanks": "Grazie per aver condiviso!",
    "error": "Ops! Qualcosa è andato storto. Puoi riprovare tra poco.",
    "empty": "Non ho ricevuto alcun testo. Puoi riprovare?",
    "not_identified": "Errore: utente non identificato.",
}
command_handlers = CommandHandlers(messages)
message_handlers = MessageHandlers(messages)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Telegram Bot Webhook",
    description="Receives updates from Telegram Bot API via webhook (secured with secret token)",
)
@limiter.limit("10/second")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None),
) -> dict[str, str]:
    """
    Handle incoming Telegram webhook updates with security validation.

    Security layers:
    1. Secret token validation (prevents unauthorized access)
    2. Rate limiting (10 req/s per IP)
    3. Request size limit (1MB max, enforced by middleware)
    4. Payload validation (Telegram Update object structure)

    Args:
        request: FastAPI request object
        x_telegram_bot_api_secret_token: Secret token from Telegram (header)

    Returns:
        Success acknowledgment

    Raises:
        HTTPException 403: Invalid or missing secret token
        HTTPException 400: Invalid payload structure
        HTTPException 500: Internal processing error
    """
    # SECURITY: Validate secret token
    expected_token = settings.telegram_webhook_secret
    if not expected_token:
        logger.error("TELEGRAM_WEBHOOK_SECRET not configured - rejecting all webhook requests")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook not properly configured",
        )

    if x_telegram_bot_api_secret_token != expected_token:
        logger.warning(
            "Invalid webhook secret token",
            remote_addr=request.client.host if request.client else "unknown",
            provided_token=x_telegram_bot_api_secret_token[:10] + "..." if x_telegram_bot_api_secret_token else None,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token",
        )

    # Parse Telegram Update object
    try:
        update_data = await request.json()
    except Exception as e:
        logger.error("Failed to parse webhook payload", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Validate Telegram Update structure
    if not isinstance(update_data, dict) or "update_id" not in update_data:
        logger.error("Invalid Telegram Update structure", payload=update_data)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram Update format",
        )

    update_id = update_data.get("update_id")
    logger.info("Received Telegram webhook update", update_id=update_id)

    # Process message update
    if "message" in update_data:
        await _process_message(update_data["message"])
    elif "edited_message" in update_data:
        # Optionally handle edited messages
        logger.debug("Ignoring edited message", update_id=update_id)
    else:
        logger.debug("Unsupported update type", update_id=update_id, keys=list(update_data.keys()))

    return {"status": "ok"}


async def _process_message(message: dict) -> None:
    """
    Process incoming Telegram message (command or text).

    Args:
        message: Telegram Message object
    """
    try:
        # Create Telegram Update and Message objects
        bot = Bot(token=settings.telegram_bot_token)

        # Build Update object from webhook data
        update = Update.de_json({"update_id": 0, "message": message}, bot)

        if not update or not update.message:
            logger.error("Failed to parse Telegram message", message=message)
            return

        # Extract message info
        user = update.message.from_user
        text = update.message.text

        logger.info(
            "Processing message",
            user_id=user.id if user else None,
            username=user.username if user else None,
            text_preview=text[:50] if text else None,
        )

        # Check if message is a command
        if text and text.startswith("/"):
            command = text.split()[0].lower()
            await _handle_command(update, command)
        elif text:
            await _handle_text(update)
        else:
            logger.debug("Non-text message received", message_type=update.message.content_type)

    except Exception as e:
        logger.error("Error processing message", error=str(e), exc_info=True)
        # Don't raise - acknowledge webhook even if processing fails
        # Telegram will retry failed webhooks, causing duplicates


async def _handle_command(update: Update, command: str) -> None:
    """Route command to appropriate handler."""
    # Create empty context (not used in webhook mode)
    class EmptyContext:
        pass

    context = EmptyContext()

    if command == "/start":
        await command_handlers.start(update, context)
    elif command == "/help":
        await command_handlers.help(update, context)
    elif command == "/ask":
        await command_handlers.ask(update, context)
    elif command == "/monthly":
        await command_handlers.monthly(update, context)
    elif command == "/exit":
        await command_handlers.exit(update, context)
    else:
        logger.debug("Unknown command", command=command)


async def _handle_text(update: Update) -> None:
    """Route text message to handler."""
    class EmptyContext:
        pass

    context = EmptyContext()
    await message_handlers.handle_text(update, context)
