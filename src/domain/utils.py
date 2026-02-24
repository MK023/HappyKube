"""Domain utility functions."""

ITALIAN_MONTH_NAMES: dict[str, str] = {
    "01": "Gennaio",
    "02": "Febbraio",
    "03": "Marzo",
    "04": "Aprile",
    "05": "Maggio",
    "06": "Giugno",
    "07": "Luglio",
    "08": "Agosto",
    "09": "Settembre",
    "10": "Ottobre",
    "11": "Novembre",
    "12": "Dicembre",
}


def get_italian_month_name(month: str) -> str:
    """
    Convert YYYY-MM format to Italian month name.

    Args:
        month: Month string in YYYY-MM format (e.g., '2026-01')

    Returns:
        Italian month name (e.g., 'Gennaio') or the original string if parsing fails
    """
    try:
        _, mon = month.split("-")
        return ITALIAN_MONTH_NAMES.get(mon, month)
    except (ValueError, KeyError):
        return month
