"""Language detection utilities."""

import re

from config import get_logger

logger = get_logger(__name__)

# Common Italian keywords for heuristic detection
ITALIAN_KEYWORDS = {
    "ciao", "bene", "male", "triste", "felice", "contento", "paura", "arrabbiato",
    "ansia", "gioia", "amore", "odio", "preoccupato", "sono", "mi sento", "oggi",
    "ieri", "domani", "non lo so", "forse", "penso", "credo", "spero", "temo",
    "felicità", "rabbia", "tristezza", "sorpresa", "disgusto", "fiducia",
    "emozione", "emozioni", "sentimento", "sentimenti", "umore", "stato d'animo",
    "stanco", "energico", "calmo", "nervoso", "rilassato", "ansioso",
}

# Emoji pattern
EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]+")


def is_emoji(text: str) -> bool:
    """
    Check if text contains only emojis and whitespace.

    Args:
        text: Input text

    Returns:
        True if text is emoji-only
    """
    stripped = text.strip()
    if not stripped:
        return False

    # Remove all emojis and check if anything is left
    without_emojis = EMOJI_PATTERN.sub("", stripped).strip()
    return len(without_emojis) == 0


def is_italian(text: str) -> bool:
    """
    Heuristic Italian language detection.

    Checks if text contains common Italian keywords.
    Not perfect, but fast and good enough for our use case.

    Args:
        text: Input text

    Returns:
        True if text appears to be Italian
    """
    text_lower = text.lower()

    # Check if any Italian keyword is present
    for keyword in ITALIAN_KEYWORDS:
        if keyword in text_lower:
            logger.debug("Detected Italian keyword", keyword=keyword)
            return True

    return False


def detect_language(text: str) -> str:
    """
    Detect language and return model type to use.

    Args:
        text: Input text

    Returns:
        "italian" or "english"
    """
    if is_emoji(text):
        # Emojis work better with English model
        logger.debug("Detected emoji input, using English model")
        return "english"

    if is_italian(text):
        logger.debug("Detected Italian language")
        return "italian"

    # Default to English
    logger.debug("Defaulting to English language")
    return "english"
