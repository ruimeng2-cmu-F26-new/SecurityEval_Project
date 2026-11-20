"""Handwritten control, not LLM output. Safe: allows http(s) URLs only and escapes both values."""
import html
from urllib.parse import urlsplit


def render_profile_link(display_name, website):
    try:
        allowed = urlsplit(website).scheme in ("http", "https") and website == website.strip() and not any(
            c in website for c in "\t\r\n")
    except ValueError:
        allowed = False
    href = html.escape(website, quote=True) if allowed else "#"
    return f'<a href="{href}">{html.escape(display_name)}</a>'
