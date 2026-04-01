"""Metadata extraction and shared parsing utilities."""
import re
from datetime import date, datetime

DATE_PATTERNS = [
    r"Last\s+update\s+date\s*:\s*(\d{2}-\d{2}-\d{4})",
    r"கடைசி\s+புதுப்பிக்கப்பட்ட\s+நாள்\s*:\s*(\d{2}-\d{2}-\d{4})",
]


def extract_last_updated(html: str) -> date | None:
    """Parse 'Last update date: 29-03-2026' from HTML → datetime.date."""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, html)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d-%m-%Y").date()
            except ValueError:
                continue
    return None


def safe_parse_number(text: str) -> float | None:
    """
    Robust numeric parsing. Returns None for unparseable values
    so callers can distinguish 'no data' from 'zero'.
    """
    if not text:
        return None
    text = text.strip()
    if text in ("", "-", "--", "N/A", "nil", "Nil", "NIL", "*"):
        return None
    text = text.replace(",", "").replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return None
