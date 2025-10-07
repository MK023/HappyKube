import os
from transformers import pipeline
from typing import Dict, Any, Iterable

SENTIMENT_LABELS = {"positive", "negative", "neutral"}

class SentimentAnalyzer:
    def __init__(self):
        model_name = os.getenv("SENTIMENT_MODEL", "MilaNLProc/feel-it-italian-sentiment")
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
            sentiment = first.get("label", "unknown")
            score = round(first.get("score", 2))
        else:
            sentiment = str(first)
            score = 0
        if sentiment not in SENTIMENT_LABELS:
            sentiment = "unknown"
        return {"sentiment": sentiment, "score": score}