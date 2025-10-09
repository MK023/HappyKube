import os
import logging
from transformers import pipeline
from typing import Dict, Any, Iterable

SENTIMENT_LABELS = {"positive", "negative", "neutral"}

class SentimentAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger("SentimentAnalyzer")
        model_name = os.getenv("SENTIMENT_MODEL", "MilaNLProc/feel-it-italian-sentiment")
        self.logger.info(f"Inizializzo pipeline transformers con modello: {model_name}")
        self.classifier = pipeline("text-classification", model=model_name) # type: ignore

    def analyze(self, text: str) -> Dict[str, Any]:
        try:
            result = self.classifier(text)
            if not isinstance(result, list):
                if isinstance(result, Iterable):
                    result = list(result)
                else:
                    result = [result]
            first = result[0] if result else {}
            if isinstance(first, dict):
                sentiment = first.get("label", "unknown")
                score = round(first.get("score", 2))
            else:
                sentiment = str(first)
                score = 0
            if sentiment not in SENTIMENT_LABELS:
                sentiment = "unknown"
            self.logger.debug(f"Testo: {text} | Risultato: {sentiment}, score: {score}")
            return {"sentiment": sentiment, "score": score}
        except Exception as e:
            self.logger.error(f"Errore nell'analisi del testo: {text} | Exception: {e}", exc_info=True)
            return {"sentiment": "unknown", "score": 0}