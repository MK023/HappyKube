import os
import configparser
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from event_logs import EventLogger
from comandi_handler import ComandiHandler
import telegram.error
from emotion_api_client import EmotionAPIClient

# load_dotenv()
config = configparser.ConfigParser()

# Prova a leggere sia da cwd che dalla cartella superiore
config_path = "config.ini"
if not os.path.exists(config_path):
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
config.read(config_path)

if "TELEGRAM" not in config:
    raise RuntimeError(f"Sezione [TELEGRAM] mancante nel file {config_path}. Contenuto attuale: {config.sections()}")

# FORZA LA LETTURA UTF-8
with open(config_path, encoding="utf-8") as f:
    config.read_file(f)

class TelegramBot:
    def __init__(self, emotion_api):
        self.token = config["TELEGRAM"]["token"]
        if not self.token or not isinstance(self.token, str):
            raise ValueError("TELEGRAM_TOKEN mancante in config.ini! Impossibile avviare il bot Telegram.")
        self.emotion_api = emotion_api
        self.logger = EventLogger(
            name="TelegramBot",
            log_filename=config["LOGGING"].get("log_filename", "telegram_bot.log")
        )
        # Passa i messaggi letti dal config.ini al gestore dei comandi
        self.comandi = ComandiHandler(self.logger, shutdown_callback=self.on_shutdown, messages=dict(config["MESSAGES"]))
        self.app = ApplicationBuilder().token(self.token).build()
        self.logger.info("TelegramBot initialized")

    async def receive_emotion(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None:
            return
        user = update.effective_user
        user_id = str(user.id) if user and getattr(user, "id", None) is not None else None
        if user_id is None:
            self.logger.warning("Tentativo di messaggio senza user_id")
            await update.message.reply_text(self.comandi.messages["not_identified"])
            return

        text = update.message.text.strip() if update.message.text else None
        if not text:
            self.logger.warning(f"Utente {user_id} ha inviato messaggio vuoto")
            await update.message.reply_text(self.comandi.messages["empty"])
            return

        try:
            result = self.emotion_api.process_emotion(user_id, text)
            self.logger.info(f"Analisi emozione per user {user_id}: testo='{text}' -> {result}")
        except Exception as e:
            self.logger.error(f"Errore analisi emozione per user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(self.comandi.messages["error"])
            return

        emotion = result.get('emotion') if result and isinstance(result, dict) else None
        score = result.get('score') if result and isinstance(result, dict) else None

        if emotion is None or score is None:
            self.logger.warning(f"Analisi fallita per user {user_id}: result={result}")
            await update.message.reply_text(self.comandi.messages["not_understood"])
            return

        await update.message.reply_text(
            f"{self.comandi.messages['thanks']}\nHo registrato: \"{text}\"\n"
            f"Emozione riconosciuta: {emotion.capitalize()} (confidenza: {score:.2f})"
        )

    def on_shutdown(self):
        self.logger.info("TelegramBot in chiusura... Arrivederci!")
        # Eventuali cleanup (DB, file, ecc.)

    def run(self):
        self.app.add_handler(CommandHandler("start", self.comandi.start))
        self.app.add_handler(CommandHandler("chiedi", self.comandi.chiedi))
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
    emotion_api = EmotionAPIClient()  # <-- ora chiama le API REST!
    bot = TelegramBot(emotion_api)
    bot.run()