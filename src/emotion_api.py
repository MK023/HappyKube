import re
import os
import logging
from transformers import pipeline
from emotion_db import EmotionDB
from emotion_analyzer import EmotionAnalyzer
from sentiment_analyzer import SentimentAnalyzer
from typing import List, Dict, Any, Optional

def is_emoji(s: str) -> bool:
    emoji_pattern = r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+"
    return bool(re.fullmatch(rf"\s*({emoji_pattern}\s*)+", s))

def is_italian(s: str) -> bool:
    # Semplice euristica: contiene almeno una parola italiana tipica
    ITALIAN_KEYWORDS = [
        "ciao", "bene", "male", "triste", "felice", 
        "contento", "paura", "arrabbiato", "ansia", 
        "gioia", "amore", "odio", "preoccupato", "porco+dio",
        "vaffanculo", "merda", "cazzo", "maledizione", "dannazione",
        "sono", "mi sento", "oggi", "ieri", "domani",
        "oggi mi sento", "ieri mi sono sentito", "domani mi sentirò",
        "non lo so", "forse", "penso", "credo", "spero", "temo", "felicità", 
        "rabbia", "tristezza", "paura", "sorpresa", "disgusto", "fiducia", "anticipazione",
        "emozione", "emozioni", "sentimento", "sentimenti", "umore", "umori", "stato d'animo",
        "mi fa arrabbiare", "mi rende felice", "mi fa paura", "mi fa tristezza", "mi fa gioia",
        "mi fa schifo", "mi sorprende", "mi fido", "mi aspetto", "mi preoccupa", "mi rende ansioso",
        "mi rende nervoso", "mi rende calmo", "mi rende rilassato", "mi rende energico",
        "mi rende stanco", "mi rende triste", "mi rende felice", "mi rende arrabbiato", "mi rende ansioso",
        "mi rende nervoso", "mi rende calmo", "mi rende rilassato", "mi rende energico", "mi rende stanco"
        
    ]
    return any(word in s.lower() for word in ITALIAN_KEYWORDS)

def get_top_emotion(results):
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
        self.logger = logging.getLogger("EmotionAPI")
        self.italian_analyzer = EmotionAnalyzer()
        distill_model_name = os.getenv("DISTILL_MODEL", "j-hartmann/emotion-english-distilroberta-base")
        self.logger.info(f"Caricamento modello distill: {distill_model_name}")
        self.distill_classifier = pipeline("text-classification", model=distill_model_name, return_all_scores=True)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.italian_db = EmotionDB(report_type="italian")
        self.distill_db = EmotionDB(report_type="distill")
        self.sentiment_db = EmotionDB(report_type="sentiment")

    def choose_model(self, text: str) -> str:
        model = "distill"
        if is_emoji(text):
            model = "distill"
        elif is_italian(text):
            model = "italian"
        self.logger.debug(f"Scelto modello '{model}' per testo: {text}")
        return model

    def process_emotion(self, user_id: str, text: str) -> Dict[str, Any]:
        model_type = self.choose_model(text)
        if model_type == "italian":
            res = self.italian_analyzer.analyze(text)
            emotion = res["emotion"]
            score = res["score"]
            try:
                self.italian_db.save_emotion(user_id, text, emotion, score)
            except Exception as e:
                self.logger.error(f"Errore salvataggio DB italiano: {e}", exc_info=True)
            self.logger.info(f"process_emotion: user_id={user_id}, text={text}, model=italian, emotion={emotion}, score={score}")
            return {"emotion": emotion, "score": score, "model": "italian"}
        else:
            results = self.distill_classifier(text)
            emotion, score = get_top_emotion(results)
            try:
                self.distill_db.save_emotion(user_id, text, emotion, score)
            except Exception as e:
                self.logger.error(f"Errore salvataggio DB distill: {e}", exc_info=True)
            self.logger.info(f"process_emotion: user_id={user_id}, text={text}, model=distill, emotion={emotion}, score={score}")
            return {"emotion": emotion, "score": score, "model": "distill"}

    def process_sentiment(self, user_id: str, text: str) -> Dict[str, Any]:
        res = self.sentiment_analyzer.analyze(text)
        sentiment = res["sentiment"]
        score = res["score"]
        try:
            self.sentiment_db.save_emotion(user_id, text, sentiment, score)
        except Exception as e:
            self.logger.error(f"Errore salvataggio DB sentiment: {e}", exc_info=True)
        self.logger.info(f"process_sentiment: user_id={user_id}, text={text}, sentiment={sentiment}, score={score}")
        return {"sentiment": sentiment, "score": score}

    def get_report(self, user_id: str, month: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        report = {}
        try:
            data = self.italian_db.get_report(user_id, month)
            report["italian"] = [{"date": str(d), "emotion": e, "score": s} for (d, e, s) in data]
        except Exception as e:
            self.logger.error(f"Errore report DB italiano: {e}", exc_info=True)
            report["italian"] = []
        try:
            data = self.distill_db.get_report(user_id, month)
            report["distill"] = [{"date": str(d), "emotion": e, "score": s} for (d, e, s) in data]
        except Exception as e:
            self.logger.error(f"Errore report DB distill: {e}", exc_info=True)
            report["distill"] = []
        try:
            data = self.sentiment_db.get_report(user_id, month)
            report["sentiment"] = [{"date": str(d), "sentiment": e, "score": s} for (d, e, s) in data]
        except Exception as e:
            self.logger.error(f"Errore report DB sentiment: {e}", exc_info=True)
            report["sentiment"] = []
        self.logger.debug(f"get_report: user_id={user_id}, month={month}")
        return report