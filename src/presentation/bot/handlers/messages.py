"""Telegram bot message handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from application.services import EmotionService
from config import get_logger
from infrastructure.cache import get_cache
from infrastructure.database import get_db_session
from infrastructure.ml import get_model_factory
from infrastructure.repositories import EmotionRepository, UserRepository

logger = get_logger(__name__)


class MessageHandlers:
    """Handlers for Telegram bot messages."""

    def __init__(self, messages: dict[str, str]) -> None:
        """
        Initialize message handlers.

        Args:
            messages: Dictionary of localized messages
        """
        self.messages = messages

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming text messages (emotion analysis).

        Args:
            update: Telegram update
            context: Bot context
        """
        if not update.message or not update.message.text:
            return

        user = update.effective_user
        if not user or not hasattr(user, "id"):
            logger.warning("Message from unknown user")
            await update.message.reply_text(
                self.messages.get("not_identified", "Utente non identificato.")
            )
            return

        user_id = str(user.id)
        text = update.message.text.strip()

        if not text:
            await update.message.reply_text(self.messages.get("empty", "Messaggio vuoto."))
            return

        try:
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

                # Analyze emotion (already async, handler is async)
                result = await service.analyze_emotion(telegram_id=user_id, text=text)

            logger.info(
                "Emotion analyzed via bot",
                user_id=user_id,
                emotion=result.emotion,
                score=result.score,
            )

            # Prepare response with emoji
            emotion_emoji = {
                "joy": "😊",
                "sadness": "😢",
                "anger": "😠",
                "fear": "😨",
                "surprise": "😲",
                "disgust": "🤢",
                "neutral": "😐",
            }.get(result.emotion, "🤔")

            response = (
                f"{self.messages.get('thanks', 'Grazie per aver condiviso!')}\n\n"
                f"📝 *Testo analizzato:* \"{text}\"\n"
                f"{emotion_emoji} *Emozione rilevata:* {result.emotion.capitalize()}\n"
                f"📊 *Confidenza:* {result.confidence}\n"
                f"🤖 *Modello:* {result.model_type}"
            )

            if result.sentiment:
                sentiment_emoji = {"positive": "👍", "negative": "👎", "neutral": "🤷"}.get(
                    result.sentiment, "❓"
                )
                response += f"\n{sentiment_emoji} *Sentiment:* {result.sentiment}"

            await update.message.reply_text(response, parse_mode="Markdown")

        except Exception as e:
            logger.error("Error analyzing emotion", error=str(e), user_id=user_id)
            await update.message.reply_text(
                self.messages.get(
                    "error", "Errore durante l'analisi. Riprova tra poco."
                )
            )
