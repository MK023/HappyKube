"""Telegram bot application."""

import os
import signal
import sys
from pathlib import Path

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import get_logger, settings, setup_logging
from .handlers import CommandHandlers, MessageHandlers

logger = get_logger(__name__)

# Lock file to prevent multiple instances
LOCK_FILE = Path("/tmp/happykube_bot.lock")


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


def acquire_lock() -> bool:
    """
    Acquire lock file to ensure single bot instance.

    Returns:
        True if lock acquired, False otherwise
    """
    if LOCK_FILE.exists():
        try:
            # Check if process is still running
            pid = int(LOCK_FILE.read_text())
            os.kill(pid, 0)  # Check if process exists
            logger.error(
                "Another bot instance is running",
                pid=pid,
                lock_file=str(LOCK_FILE)
            )
            return False
        except (ProcessLookupError, ValueError):
            # Process not running, remove stale lock
            logger.warning("Removing stale lock file", lock_file=str(LOCK_FILE))
            LOCK_FILE.unlink()

    # Create lock file with current PID
    LOCK_FILE.write_text(str(os.getpid()))
    logger.info("Lock acquired", pid=os.getpid(), lock_file=str(LOCK_FILE))
    return True


def release_lock() -> None:
    """Release lock file."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
        logger.info("Lock released", lock_file=str(LOCK_FILE))


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down gracefully")
    release_lock()
    sys.exit(0)


def create_bot() -> None:
    """Create and run Telegram bot with single-instance protection."""
    # Setup logging
    setup_logging()

    # Acquire lock to prevent multiple instances
    if not acquire_lock():
        logger.error("Failed to acquire lock, exiting")
        sys.exit(1)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        logger.info(
            "Starting Telegram bot",
            env=settings.app_env,
            version=settings.app_version,
            pid=os.getpid(),
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
        app.add_handler(CommandHandler("exit", command_handlers.exit))

        # Register message handler (non-command text)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.handle_text))

        logger.info("Telegram bot initialized, starting polling")

        # Run bot
        app.run_polling(allowed_updates=["message"])

    except Exception as e:
        logger.error("Bot crashed", error=str(e), exc_info=True)
        raise
    finally:
        release_lock()


if __name__ == "__main__":
    create_bot()
