"""ML model type enumeration."""

from enum import Enum


class ModelType(str, Enum):
    """Available ML model types."""

    ITALIAN_EMOTION = "italian_emotion"
    ENGLISH_EMOTION = "english_emotion"
    SENTIMENT = "sentiment"
    GROQ = "groq"

    @property
    def display_name(self) -> str:
        """Get human-readable model name."""
        return {
            self.ITALIAN_EMOTION: "Italian Emotion Classifier",
            self.ENGLISH_EMOTION: "English Emotion Classifier",
            self.SENTIMENT: "Sentiment Analyzer",
            self.GROQ: "Groq Llama 3.3",
        }[self]
