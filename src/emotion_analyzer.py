import os
from transformers import pipeline
from typing import Dict, Any, Iterable

EMOTION_LABELS = {"anger", "joy", "sadness", "fear"}

class EmotionAnalyzer:
    def __init__(self):
        model_name = os.getenv("EMOTION_MODEL", "MilaNLProc/feel-it-italian-emotion")
        self.classifier = pipeline("text-classification", model=model_name)

    def analyze(self, text: str) -> Dict[str, Any]:
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
        return {"emotion": emotion, "score": score}