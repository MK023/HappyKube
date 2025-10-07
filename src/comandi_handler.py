import sys

class ComandiHandler:
    def __init__(self, logger, shutdown_callback=None, messages=None):
        self.logger = logger
        self.shutdown_callback = shutdown_callback
        self.messages = messages or {}

    async def start(self, update, context):
        user_id = update.effective_user.id if update.effective_user else "unknown"
        self.logger.info(f"/start richiesto da user {user_id}", context="ComandiHandler")
        await update.message.reply_text(self.messages.get("welcome", "Ciao! 😊 Sono HappyKube.\nDimmi come ti senti oggi!"))

    async def chiedi(self, update, context):
        user_id = update.effective_user.id if update.effective_user else "unknown"
        self.logger.info(f"/chiedi richiesto da user {user_id}", context="ComandiHandler")
        await update.message.reply_text(self.messages.get("ask_emotion", "Dimmi come ti senti, sono qui per ascoltarti!"))

    async def exit(self, update, context):
        user_id = update.effective_user.id if update.effective_user else "unknown"
        self.logger.info(f"/exit richiesto da user {user_id}", context="ComandiHandler")
        await update.message.reply_text(self.messages.get("exit", "Bot in chiusura gentile. Grazie per aver usato HappyKube! 🫶"))
        if self.shutdown_callback:
            self.shutdown_callback()
        sys.exit(0)

    async def help(self, update, context):
        user_id = update.effective_user.id if update.effective_user else "unknown"
        self.logger.info(f"/help richiesto da user {user_id}", context="ComandiHandler")
        await update.message.reply_text(
            "Comandi disponibili:\n"
            "/start - Messaggio di benvenuto\n"
            "/chiedi - Chiedi come ti senti\n"
            "/exit - Chiudi il bot\n"
            "/help - Mostra questo messaggio"
        )