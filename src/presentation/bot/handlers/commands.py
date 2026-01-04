"""Telegram bot command handlers."""

import httpx
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from config import get_logger, get_settings

logger = get_logger(__name__)
settings = get_settings()


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
/monthly - Statistiche del mese corrente
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

    async def monthly(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle /monthly command - get current month statistics.

        Args:
            update: Telegram update
            context: Bot context
        """
        if not update.message:
            return

        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Errore: utente non identificato.")
            return

        telegram_id = str(user.id)
        current_month = datetime.now().strftime("%Y-%m")

        logger.info(
            "User requested monthly stats",
            user_id=telegram_id,
            month=current_month
        )

        await update.message.reply_text("📊 Recupero le tue statistiche mensili...")

        try:
            # Call internal API endpoint
            api_url = f"http://localhost:{settings.api_port}/reports/monthly/{telegram_id}/{current_month}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url)

            if response.status_code == 404:
                await update.message.reply_text(
                    "📭 Nessun dato disponibile per questo mese.\n\n"
                    "Inizia a condividere le tue emozioni e torna tra qualche giorno!"
                )
                return

            if response.status_code != 200:
                logger.error(
                    "Failed to fetch monthly stats",
                    status_code=response.status_code
                )
                await update.message.reply_text(
                    "❌ Errore nel recupero delle statistiche. Riprova tra poco."
                )
                return

            data = response.json()

            # Format statistics message
            msg = f"📊 *Statistiche {current_month}*\n\n"
            msg += f"📝 Messaggi totali: {data['total_messages']}\n"
            msg += f"📅 Giorni attivi: {data['active_days']}\n\n"

            # Top 3 emotions
            emotions = sorted(
                data['emotions'].items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:3]

            msg += "*🎭 Top 3 Emozioni:*\n"
            for emotion_name, stats in emotions:
                emoji = self._get_emotion_emoji(emotion_name)
                msg += (
                    f"{emoji} {emotion_name.title()}: {stats['count']} "
                    f"({stats['percentage']}%)\n"
                )

            # Insights
            if data.get('insights'):
                msg += "\n*💡 Insights:*\n"
                for insight in data['insights'][:3]:
                    msg += f"• {insight['message']}\n"

            await update.message.reply_text(msg, parse_mode="Markdown")

        except httpx.TimeoutException:
            logger.error("Timeout fetching monthly stats")
            await update.message.reply_text(
                "⏱️ Timeout nel recupero delle statistiche. Riprova."
            )
        except Exception as e:
            logger.error("Error in monthly command", error=str(e), exc_info=True)
            await update.message.reply_text(
                "❌ Si è verificato un errore. Riprova più tardi."
            )

    @staticmethod
    def _get_emotion_emoji(emotion: str) -> str:
        """Get emoji for emotion type."""
        emotion_emojis = {
            "joy": "😊",
            "sadness": "😢",
            "anger": "😠",
            "fear": "😨",
            "surprise": "😲",
            "disgust": "🤢",
            "neutral": "😐",
            "love": "❤️"
        }
        return emotion_emojis.get(emotion.lower(), "🎭")
