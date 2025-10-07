import os
from flask import Flask, request, jsonify

# Per caricare le variabili d'ambiente dal file .env
from dotenv import load_dotenv
load_dotenv()

from emotion_api import EmotionAPI

app = Flask(__name__)
emotion_api = EmotionAPI()

@app.route("/")
def home():
    return "Hello from HappyKube Python Bot!"

@app.route("/emotion", methods=["POST"])
def emotion():
    data = request.get_json()
    user_id = data.get("user_id", "anonimo")
    text = data.get("text", "")
    result = emotion_api.process_emotion(user_id, text)
    return jsonify(result)

@app.route("/report", methods=["GET"])
def report():
    user_id = request.args.get("user_id", "anonimo")
    month = request.args.get("month", None)
    report = emotion_api.get_report(user_id, month)
    return jsonify(report)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))