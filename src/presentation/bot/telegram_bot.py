"""Telegram bot application."""

import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import get_logger, settings, setup_logging
from .handlers import CommandHandlers, MessageHandlers

logger = get_logger(__name__)


# Load messages from environment (K8s ConfigMap) or use defaults
DEFAULT_MESSAGES = {
    "welcome": "Ciao! 😊 Sono HappyKube! Dimmi come ti senti oggi!",
    "ask_emotion": "Dimmi come ti senti, sono qui per ascoltarti!",
    "thanks": "Grazie per aver condiviso!",
    "error": "Ops! Qualcosa è andato storto. Puoi riprovare tra poco.",
    "empty": "Non ho ricevuto alcun testo. Puoi riprovare?",
    "not_identified": "Errore: utente non identificato.",
}


def load_messages() -> dict[str, str]:
    """
    Load messages from environment variables.

    Returns:
        Dictionary of messages
    """
    messages = DEFAULT_MESSAGES.copy()

    # Override with env vars (from K8s ConfigMap)
    for key in DEFAULT_MESSAGES.keys():
        env_key = f"MESSAGES_{key.upper()}"
        if env_value := os.getenv(env_key):
            messages[key] = env_value

    return messages


def create_bot() -> None:
    """Create and run Telegram bot."""
    # Setup logging
    setup_logging()

    logger.info(
        "Starting Telegram bot",
        env=settings.app_env,
        version=settings.app_version,
    )

    # Load messages
    messages = load_messages()

    # Create handlers
    command_handlers = CommandHandlers(messages)
    message_handlers = MessageHandlers(messages)

    # Build application
    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", command_handlers.start))
    app.add_handler(CommandHandler("help", command_handlers.help))
    app.add_handler(CommandHandler("ask", command_handlers.ask))

    # Register message handler (non-command text)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text))

    logger.info("Telegram bot initialized, starting polling")

    # Run bot
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    create_bot()
