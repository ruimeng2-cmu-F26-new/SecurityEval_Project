"""Handwritten control, not LLM output. Safe: compares the parsed host name."""
from urllib.parse import urlsplit


def is_allowed_url(url):
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and (host == "example.com" or host.endswith(".example.com"))
