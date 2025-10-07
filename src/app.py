import os
import logging
import sys
from flask import Flask, request, jsonify

from dotenv import load_dotenv
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s %(levelname)s %(name)s %(message)s")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)

from emotion_api import EmotionAPI
from event_logger import EventLogger

app = Flask(__name__)
emotion_api = EmotionAPI()
logger = EventLogger("happykube-main")
logger.info("Applicazione HappyKube avviata!")

@app.route("/")
def home():
    logger.info("Chiamata GET su /", context="Flask")
    return "Hello from HappyKube Python Bot!"

@app.route("/emotion", methods=["POST"])
def emotion():
    data = request.get_json()
    user_id = data.get("user_id", "anonimo")
    text = data.get("text", "")
    logger.info(f"Richiesta emotion da user {user_id}", context="Flask", text=text)
    result = emotion_api.process_emotion(user_id, text)
    return jsonify(result)

@app.route("/report", methods=["GET"])
def report():
    user_id = request.args.get("user_id", "anonimo")
    month = request.args.get("month", None)
    logger.info(f"Richiesta report da user {user_id}", context="Flask", month=month)
    report = emotion_api.get_report(user_id, month)
    return jsonify(report)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))