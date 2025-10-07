import os
import logging
import requests

class EmotionAPIClient:
    def __init__(self, api_url=None):
        self.api_url = api_url or os.environ.get("EMOTION_API_URL", "http://localhost:5000")
        self.logger = logging.getLogger("EmotionAPIClient")

    def process_emotion(self, user_id, text):
        try:
            resp = requests.post(
                f"{self.api_url}/emotion",
                json={"user_id": user_id, "text": text},
                timeout=10
            )
            resp.raise_for_status()
            self.logger.debug(f"process_emotion: user_id={user_id}, text={text}, status={resp.status_code}")
            return resp.json()
        except Exception as e:
            self.logger.error(f"Errore chiamata emotion_api /emotion: {e}", exc_info=True)
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
            self.logger.debug(f"get_report: user_id={user_id}, month={month}, status={resp.status_code}")
            return resp.json()
        except Exception as e:
            self.logger.error(f"Errore chiamata emotion_api /report: {e}", exc_info=True)
            return {}