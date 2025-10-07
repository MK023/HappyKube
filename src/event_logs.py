import os
import logging
from logging.handlers import RotatingFileHandler
import json

class EventLogger:
    def __init__(
        self,
        name="EventLogger",
        log_filename="event.log",
        log_dir=None,
        level=logging.INFO,
        fmt='%(asctime)s %(levelname)s %(name)s %(message)s'
    ):
        # Cartella logs fuori da src, default: ../logs
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, log_filename)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        formatter = logging.Formatter(fmt)

        # Evita handler duplicati
        if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == log_path for h in self.logger.handlers):
            file_handler = RotatingFileHandler(log_path, maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            self.logger.addHandler(file_handler)

        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            self.logger.addHandler(console_handler)

    def info(self, msg, context=None, **kwargs):
        self.logger.info(self._format_msg(msg, context, kwargs))

    def warning(self, msg, context=None, **kwargs):
        self.logger.warning(self._format_msg(msg, context, kwargs))

    def error(self, msg, context=None, exc_info=False, **kwargs):
        self.logger.error(self._format_msg(msg, context, kwargs), exc_info=exc_info)

    def debug(self, msg, context=None, **kwargs):
        self.logger.debug(self._format_msg(msg, context, kwargs))

    def flush(self):
        """Flush all handlers (utile per test o shutdown)."""
        for handler in self.logger.handlers:
            handler.flush()

    def _format_msg(self, msg, context, kwargs):
        """
        Rende il messaggio log strutturato.
        - msg: stringa base
        - context: stringa opzionale (es: 'DB', 'TelegramBot', ecc.)
        - kwargs: altri dati (es: dict, id utente, metriche)
        """
        parts = []
        if context:
            parts.append(f"[{context}]")
        parts.append(str(msg))
        if kwargs:
            parts.append(" | " + json.dumps(kwargs, ensure_ascii=False))
        return " ".join(parts)

    def json_log(self, level, msg, context=None, **kwargs):
        """Logga in formato JSON (facile da integrare con ELK, Datadog, ecc.)"""
        record = {
            "msg": msg,
            "context": context,
            "level": logging.getLevelName(level),
            "extra": kwargs
        }
        self.logger.log(level, json.dumps(record, ensure_ascii=False))