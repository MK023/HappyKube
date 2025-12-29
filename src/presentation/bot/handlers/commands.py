"""Telegram bot command handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from config import get_logger

logger = get_logger(__name__)


class CommandHandlers:
    """Handlers for Telegram bot commands."""

    def __init__(self, messages: dict[str, str]) -> None:
        """
        Initialize command handlers.

        Args:
            messages: Dictionary of localized messages
        """
        self.messages = messages

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /start command.

        Args:
            update: Telegram update
            context: Bot context
        """
        if not update.message:
            return

        user = update.effective_user
        username = user.username if user else "Unknown"

        logger.info("User started bot", user_id=user.id if user else None, username=username)

        welcome_msg = self.messages.get(
            "welcome", "Ciao! Sono HappyKube! Dimmi come ti senti oggi!"
        )

        await update.message.reply_text(welcome_msg)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /help command.

        Args:
            update: Telegram update
            context: Bot context
        """
        if not update.message:
            return

        help_text = """
🤖 *HappyKube Bot - Comandi Disponibili*

📝 *Comandi Base:*
/start - Inizia conversazione
/help - Mostra questo messaggio
/ask - Chiedi come ti senti
/exit - Termina conversazione

💬 *Come usare il bot:*
Invia semplicemente un messaggio descrivendo come ti senti, e io analizzerò la tua emozione!

Esempi:
- "Oggi mi sento molto felice!"
- "Sono un po' triste"
- "Mi sento ansioso"
- 😊 (anche emoji funzionano!)

🔒 *Privacy:*
I tuoi messaggi sono criptati e sicuri.
"""

        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /ask command.

        Args:
            update: Telegram update
            context: Bot context
        """
        if not update.message:
            return

        ask_msg = self.messages.get(
            "ask_emotion", "Dimmi come ti senti, sono qui per ascoltarti!"
        )

        await update.message.reply_text(ask_msg)

    async def exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /exit command - graceful conversation end.

        Args:
            update: Telegram update
            context: Bot context
        """
        if not update.message:
            return

        user = update.effective_user
        username = user.username if user else "Unknown"

        logger.info("User exited conversation", user_id=user.id if user else None, username=username)

        goodbye_msg = self.messages.get(
            "goodbye",
            "Grazie per aver usato HappyKube! 👋\n\n"
            "Torna quando vuoi per condividere le tue emozioni.\n"
            "Ricorda: /start per ricominciare!"
        )

        await update.message.reply_text(goodbye_msg)
