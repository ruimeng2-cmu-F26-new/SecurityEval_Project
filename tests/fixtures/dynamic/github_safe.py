"""Handwritten control, not LLM output. Safe: percent-encodes the identifier as one path segment."""
from urllib.parse import quote


def build_user_api_url(user_id):
    if user_id in ("", ".", ".."):
        raise ValueError("invalid user id")
    return "https://api.github.com/users/" + quote(user_id, safe="")
