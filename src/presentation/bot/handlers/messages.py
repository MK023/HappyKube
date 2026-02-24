"""Telegram bot message handlers."""

from telegram import Bot, Update
from telegram.ext import ContextTypes

from application.services import EmotionService
from config import get_logger
from infrastructure.cache import get_cache
from infrastructure.database import get_db_session
from infrastructure.ml import get_model_factory
from infrastructure.repositories import EmotionRepository, UserRepository

logger = get_logger(__name__)

MAX_TEXT_LENGTH = 500


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
        chat_id = update.message.chat_id

        if not text:
            await update.message.reply_text(self.messages.get("empty", "Messaggio vuoto."))
            return

        # Enforce text length limit
        if len(text) > MAX_TEXT_LENGTH:
            await self._send_message(
                context,
                chat_id,
                f"Il messaggio è troppo lungo (max {MAX_TEXT_LENGTH} caratteri). Accorcialo!",
            )
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

                # Analyze emotion
                result = await service.analyze_emotion(telegram_id=user_id, text=text)

            logger.info(
                "Emotion analyzed via bot",
                user_id=user_id,
                emotion=result.emotion,
                score=result.score,
            )

            # Delete user message for privacy (only after successful analysis)
            try:
                await update.message.delete()
            except Exception:
                logger.debug("Could not delete user message", user_id=user_id)

            # Prepare response with emoji
            from domain.enums.emotion_emojis import EMOTION_EMOJIS

            emotion_emoji = EMOTION_EMOJIS.get(result.emotion, "🤔")

            response = (
                f"{self.messages.get('thanks', 'Grazie per aver condiviso!')}\n\n"
                f"{emotion_emoji} *Emozione rilevata:* {result.emotion.capitalize()}\n"
                f"📊 *Confidenza:* {result.confidence}\n"
                f"🤖 *Modello:* {result.model_type}"
            )

            if result.sentiment and result.sentiment not in ("unknown", ""):
                sentiment_emoji = {"positive": "👍", "negative": "👎", "neutral": "🤷"}.get(
                    result.sentiment, "🤷"
                )
                response += f"\n{sentiment_emoji} *Sentiment:* {result.sentiment}"

            # Send to chat directly (message may have been deleted)
            await self._send_message(context, chat_id, response, parse_mode="Markdown")

        except (ConnectionError, OSError) as e:
            logger.error(
                "Service connectivity error during analysis", error=str(e), user_id=user_id
            )
            await self._send_message(
                context,
                chat_id,
                self.messages.get("error", "Errore durante l'analisi. Riprova tra poco."),
            )
        except Exception as e:
            logger.error(
                "Unexpected error analyzing emotion", error=str(e), user_id=user_id, exc_info=True
            )
            await self._send_message(
                context,
                chat_id,
                self.messages.get("error", "Errore durante l'analisi. Riprova tra poco."),
            )

    @staticmethod
    async def _send_message(
        context: ContextTypes.DEFAULT_TYPE,
        chat_id: int,
        text: str,
        parse_mode: str | None = None,
    ) -> None:
        """Send message via bot, handling both real context and webhook context."""
        bot: Bot = context.bot  # type: ignore[assignment]
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
