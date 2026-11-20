"""Handwritten control, not LLM output. Vulnerable: unanchored host suffix and unescaped dot in a regular expression."""
import re


def is_allowed_url(url):
    return re.match(r"^https?://([a-z0-9.-]*)example.com(:\d+)?(/.*)?$", url) is not None
