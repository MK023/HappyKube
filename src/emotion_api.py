from transformers import pipeline
from emotion_db import EmotionDB
from emotion_analyzer import EmotionAnalyzer
from sentiment_analyzer import SentimentAnalyzer
from typing import List, Dict, Any, Optional
import re
import os

def is_emoji(s: str) -> bool:
    # True se il testo è solo emoji (nessuna lettera)
    emoji_pattern = r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+"
    return bool(re.fullmatch(rf"\s*({emoji_pattern}\s*)+", s))

def is_italian(s: str) -> bool:
    # Semplice euristica: contiene almeno una parola italiana tipica
    ITALIAN_KEYWORDS = [
        "ciao", "bene", "male", "triste", "felice", "contento", "paura", "arrabbiato", "ansia", "gioia", "amore", "odio", "preoccupato"
    ]
    return any(word in s.lower() for word in ITALIAN_KEYWORDS)

def get_top_emotion(results):
    # Gestione robusta per modelli HuggingFace (return_all_scores o normale)
    if results and isinstance(results[0], list):
        scores = results[0]
    elif results and isinstance(results[0], dict):
        scores = results
    else:
        return None, None
    top_emotion = max(scores, key=lambda x: x['score'])
    emotion = top_emotion["label"]
    score = round(top_emotion["score"], 2)
    return emotion, score

class EmotionAPI:
    def __init__(self):
        # Modello italiano (Feel-it)
        self.italian_analyzer = EmotionAnalyzer()
        # Modello distill (english+emoji)
        distill_model_name = os.getenv("DISTILL_MODEL", "j-hartmann/emotion-english-distilroberta-base")
        self.distill_classifier = pipeline("text-classification", model=distill_model_name, return_all_scores=True)
        # Sentiment
        self.sentiment_analyzer = SentimentAnalyzer()
        # DB separati per report
        self.italian_db = EmotionDB(report_type="italian")
        self.distill_db = EmotionDB(report_type="distill")
        self.sentiment_db = EmotionDB(report_type="sentiment")

    def choose_model(self, text: str) -> str:
        if is_emoji(text):
            return "distill"
        elif is_italian(text):
            return "italian"
        else:
            return "distill"

    def process_emotion(self, user_id: str, text: str) -> Dict[str, Any]:
        model_type = self.choose_model(text)
        if model_type == "italian":
            res = self.italian_analyzer.analyze(text)
            emotion = res["emotion"]
            score = res["score"]
            self.italian_db.save_emotion(user_id, text, emotion, score)
            return {"emotion": emotion, "score": score, "model": "italian"}
        else:
            results = self.distill_classifier(text)
            emotion, score = get_top_emotion(results)
            self.distill_db.save_emotion(user_id, text, emotion, score)
            return {"emotion": emotion, "score": score, "model": "distill"}

    def process_sentiment(self, user_id: str, text: str) -> Dict[str, Any]:
        res = self.sentiment_analyzer.analyze(text)
        sentiment = res["sentiment"]
        score = res["score"]
        self.sentiment_db.save_emotion(user_id, text, sentiment, score)
        return {"sentiment": sentiment, "score": score}

    def get_report(self, user_id: str, month: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        report = {}
        # Emozioni italiane
        data = self.italian_db.get_report(user_id, month)
        report["italian"] = [{"date": str(d), "emotion": e, "score": s} for (d, e, s) in data]
        # Emozioni distill
        data = self.distill_db.get_report(user_id, month)
        report["distill"] = [{"date": str(d), "emotion": e, "score": s} for (d, e, s) in data]
        # Sentiment
        data = self.sentiment_db.get_report(user_id, month)
        report["sentiment"] = [{"date": str(d), "sentiment": e, "score": s} for (d, e, s) in data]
        return report