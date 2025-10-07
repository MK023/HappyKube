import os
import logging
from transformers import pipeline
from typing import Dict, Any, Iterable

EMOTION_LABELS = {"anger", "joy", "sadness", "fear"}

class EmotionAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger("EmotionAnalyzer")
        model_name = os.getenv("EMOTION_MODEL", "MilaNLProc/feel-it-italian-emotion")
        self.logger.info(f"Inizializzo pipeline transformers con modello: {model_name}")
        self.classifier = pipeline("text-classification", model=model_name)

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
                emotion = first.get("label", "unknown")
                score = round(first.get("score", 2))
            else:
                emotion = str(first)
                score = 0
            if emotion not in EMOTION_LABELS:
                emotion = "unknown"
            self.logger.debug(f"Testo: {text} | Risultato: {emotion}, score: {score}")
            return {"emotion": emotion, "score": score}
        except Exception as e:
            self.logger.error(f"Errore nell'analisi del testo: {text} | Exception: {e}", exc_info=True)
            return {"emotion": "unknown", "score": 0}