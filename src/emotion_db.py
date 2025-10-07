import os
import psycopg2
import time
from datetime import datetime
from event_logs import EventLogger

class EmotionDB:
    def __init__(self, report_type=None):
        self.conn_params = dict(
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DB_PORT", 5432)
        )
        self.logger = EventLogger(name="EmotionDB", log_filename="emotion_db.log")
        self.report_type = report_type  # "italian", "distill", "sentiment"
        self.logger.info(f"EmotionDB initialized with connection params: {self.conn_params} and report_type={self.report_type}")

    def _get_conn(self):
        try:
            self.logger.debug(f"Attempting DB connection with params: {self.conn_params}")
            conn = psycopg2.connect(**self.conn_params)  # type: ignore
            self.logger.info("Database connection established")
            return conn
        except Exception as e:
            self.logger.error(f"Errore di connessione al database: {e}", exc_info=True)
            raise

    def save_emotion(self, user_id, text, emotion, score):
        start_time = time.time()
        query = (
            "INSERT INTO emotions (user_id, date, text, emotion, score, model_type) VALUES (%s, %s, %s, %s, %s, %s)"
        )
        params = (user_id, datetime.now(), text, emotion, score, self.report_type)
        self.logger.debug(f"save_emotion called | user_id={user_id} | text='{text}' | emotion={emotion} | score={score} | model={self.report_type}")
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    self.logger.debug(f"Executing query: {query} | params={params}")
                    cur.execute(query, params)
                    conn.commit()
                    elapsed = time.time() - start_time
                    self.logger.info(
                        f"Emotion salvata per user_id={user_id}, emotion={emotion}, score={score}, text='{text}', model={self.report_type} | duration={elapsed:.3f}s"
                    )
        except psycopg2.Warning as w:
            self.logger.warning(f"Warning DB (save_emotion): {w}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Errore salvataggio emozione per user_id={user_id}, text='{text}': {e}", exc_info=True)

    def get_report(self, user_id, month=None):
        start_time = time.time()
        if month:
            query = (
                "SELECT date, emotion, score FROM emotions WHERE user_id=%s AND to_char(date, 'YYYY-MM')=%s AND model_type=%s"
            )
            params = (user_id, month, self.report_type)
        else:
            query = "SELECT date, emotion, score FROM emotions WHERE user_id=%s AND model_type=%s"
            params = (user_id, self.report_type)
        self.logger.debug(f"get_report called | user_id={user_id} | month={month} | model={self.report_type}")
        try:
            with self._get_conn() as conn:
                with conn.cursor() as cur:
                    self.logger.debug(f"Executing query: {query} | params={params}")
                    cur.execute(query, params)
                    result = cur.fetchall()
                    elapsed = time.time() - start_time
                    self.logger.info(
                        f"Report estratto per user_id={user_id}, month={month}, model={self.report_type} | rows={len(result)} | duration={elapsed:.3f}s"
                )
                return result
        except psycopg2.Warning as w:
            self.logger.warning(f"Warning DB (get_report): {w}", exc_info=True)
            return []
        except Exception as e:
            self.logger.error(f"Errore report per user_id={user_id}, month={month}: {e}", exc_info=True)
            return []