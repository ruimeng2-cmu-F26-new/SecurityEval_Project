import html
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = {"http", "https"}


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    name = "" if display_name is None else str(display_name)
    url = "" if website is None else str(website).strip()

    safe_text = html.escape(name, quote=True)

    # Only permit safe, explicit web schemes (or scheme-less relative URLs),
    # preventing javascript:, data:, vbscript:, etc.
    cleaned = "".join(ch for ch in url if ch not in "\x00\t\r\n")
    try:
        parts = urlsplit(cleaned)
        scheme = parts.scheme.lower()
    except ValueError:
        return safe_text

    if scheme and scheme not in _ALLOWED_SCHEMES:
        return safe_text

    # Reject control characters and a colon appearing before any path
    # separator when no scheme was recognised (ambiguous scheme-like input).
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in cleaned):
        return safe_text
    if not scheme and ":" in cleaned.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]:
        return safe_text

    if not cleaned:
        return safe_text

    safe_href = html.escape(cleaned, quote=True)
    return f'<a href="{safe_href}" rel="noopener noreferrer nofollow">{safe_text}</a>'
