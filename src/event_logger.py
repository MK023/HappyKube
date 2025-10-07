import logging
import json

class EventLogger:
    def __init__(self, name="EventLogger"):
        self.logger = logging.getLogger(name)

    def info(self, msg, context=None, **kwargs):
        self.logger.info(self._format_msg(msg, context, kwargs))

    def warning(self, msg, context=None, **kwargs):
        self.logger.warning(self._format_msg(msg, context, kwargs))

    def error(self, msg, context=None, exc_info=False, **kwargs):
        self.logger.error(self._format_msg(msg, context, kwargs), exc_info=exc_info)

    def debug(self, msg, context=None, **kwargs):
        self.logger.debug(self._format_msg(msg, context, kwargs))

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

    def _format_msg(self, msg, context, kwargs):
        parts = []
        if context:
            parts.append(f"[{context}]")
        parts.append(str(msg))
        if kwargs:
            parts.append(" | " + json.dumps(kwargs, ensure_ascii=False))
        return " ".join(parts)

    def json_log(self, level, msg, context=None, **kwargs):
        record = {
            "msg": msg,
            "context": context,
            "level": logging.getLevelName(level),
            "extra": kwargs
        }
        self.logger.log(level, json.dumps(record, ensure_ascii=False))