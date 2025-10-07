import os
import requests

class EmotionAPIClient:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.environ.get("EMOTION_API_URL", "http://localhost:5000")

    def process_emotion(self, user_id, text):
        try:
            resp = requests.post(
                f"{self.api_url}/emotion",
                json={"user_id": user_id, "text": text},
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Errore chiamata emotion_api: {e}")
            return {}

    def get_report(self, user_id, month=None):
        params = {"user_id": user_id}
        if month:
            params["month"] = month
        try:
            resp = requests.get(
                f"{self.api_url}/report",
                params=params,
                timeout=10
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Errore chiamata emotion_api: {e}")
            return {}