import os
import configparser


from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from event_logger import EventLogger
from comandi_handler import ComandiHandler
import telegram.error
from emotion_api_client import EmotionAPIClient

# --- Lettura configurazione (INI in locale, ConfigMap ENV in K8s) ---

config = configparser.ConfigParser()


config_path = "config.ini"
if not os.path.exists(config_path):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

messages_dict = {}
telegram_token = os.environ.get("TELEGRAM_TOKEN")

# Tenta di leggere il file INI solo se esiste
if os.path.exists(config_path):
    config.read(config_path, encoding="utf-8")
    # Telegram token da file se non trovato in ENV
    if not telegram_token and "TELEGRAM" in config and "token" in config["TELEGRAM"]:
        telegram_token = config["TELEGRAM"]["token"]
    # Messaggi da file (sezione MESSAGES)
    if "MESSAGES" in config:
        messages_dict = dict(config["MESSAGES"])
else:
    # Se il file non esiste, recupera i messaggi dalle variabili d'ambiente (ConfigMap K8s)
    # Prefisso MESSAGES_ per tutte le chiavi
    keys = [
        "welcome", "ask_emotion", "exit", "not_identified",
        "empty", "error", "not_understood", "thanks"
    ]
    for key in keys:
        env_key = f"MESSAGES_{key.upper()}"
        value = os.environ.get(env_key)
        if value:
            messages_dict[key] = value

if not telegram_token or not isinstance(telegram_token, str):
    raise RuntimeError(
        "TELEGRAM_TOKEN non trovato né come variabile d'ambiente né in config.ini! Impossibile avviare il bot Telegram."
    )

class TelegramBot:
    def __init__(self, emotion_api):
        self.token = telegram_token
        self.emotion_api = emotion_api
        self.logger = EventLogger(name="TelegramBot")
        self.comandi = ComandiHandler(self.logger, shutdown_callback=self.on_shutdown, messages=messages_dict)
        self.app = ApplicationBuilder().token(self.token).build() # type: ignore
        self.logger.info("TelegramBot initialized")

    async def receive_emotion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None:
            return
        user = update.effective_user
        user_id = str(user.id) if user and getattr(user, "id", None) is not None else None
        if user_id is None:
            self.logger.warning("Tentativo di messaggio senza user_id")
            await update.message.reply_text(self.comandi.messages.get("not_identified", "Utente non identificato."))
            return

        text = update.message.text.strip() if update.message.text else None
        if not text:
            self.logger.warning(f"Utente {user_id} ha inviato messaggio vuoto")
            await update.message.reply_text(self.comandi.messages.get("empty", "Messaggio vuoto."))
            return

        try:
            result = self.emotion_api.process_emotion(user_id, text)
            self.logger.info(f"Analisi emozione per user {user_id}: testo='{text}' -> {result}")
        except Exception as e:
            self.logger.error(f"Errore analisi emozione per user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(self.comandi.messages.get("error", "Errore durante l'analisi."))
            return

        emotion = result.get('emotion') if result and isinstance(result, dict) else None
        score = result.get('score') if result and isinstance(result, dict) else None

        if emotion is None or score is None:
            self.logger.warning(f"Analisi fallita per user {user_id}: result={result}")
            await update.message.reply_text(self.comandi.messages.get("not_understood", "Non ho capito l'emozione."))
            return

        await update.message.reply_text(
            f"{self.comandi.messages.get('thanks', 'Grazie!')}\nHo registrato: \"{text}\"\n"
            f"Emozione riconosciuta: {emotion.capitalize()} (confidenza: {score:.2f})"
        )

    def on_shutdown(self):
        self.logger.info("TelegramBot in chiusura... Arrivederci!")
        

    def run(self):
        self.app.add_handler(CommandHandler("start", self.comandi.start))
        self.app.add_handler(CommandHandler("ask", self.comandi.ask))
        self.app.add_handler(CommandHandler("exit", self.comandi.exit))
        self.app.add_handler(CommandHandler("help", self.comandi.help))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_emotion))
        try:
            self.app.run_polling()
            self.logger.info("Chiusura normale del bot (run_polling terminato).")
        except telegram.error.TimedOut:
            self.logger.error("Chiusura per timeout di rete con Telegram (TimedOut).", exc_info=True)
            self.on_shutdown()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Chiusura per interruzione manuale (KeyboardInterrupt/SystemExit)")
            self.on_shutdown()
            raise
        except Exception as e:
            self.logger.error(f"Chiusura per errore inatteso: {e}", exc_info=True)
            self.on_shutdown()
            raise

if __name__ == "__main__":
    emotion_api = EmotionAPIClient()
    bot = TelegramBot(emotion_api)
    bot.run()