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

    # Only allow safe URL schemes to avoid javascript:, data:, etc.
    # Reject control characters/whitespace inside the URL that browsers may strip.
    safe_url = ""
    if url and not any(ord(c) < 32 or ord(c) == 127 for c in url):
        try:
            parts = urlsplit(url)
        except ValueError:
            parts = None
        if parts is not None and parts.scheme.lower() in _ALLOWED_SCHEMES and parts.netloc:
            safe_url = url

    if not safe_url:
        return safe_text

    safe_href = html.escape(safe_url, quote=True)
    return f'<a href="{safe_href}" rel="noopener noreferrer nofollow">{safe_text}</a>'
