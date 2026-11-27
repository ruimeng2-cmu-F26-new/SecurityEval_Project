from html import escape
from urllib.parse import urlsplit

_ALLOWED_SCHEMES = {"http", "https"}


def _sanitize_url(url: str) -> str:
    """Return a safe URL, or '#' if the URL scheme is not allowed."""
    if not isinstance(url, str):
        return "#"
    cleaned = "".join(ch for ch in url.strip() if ord(ch) > 32 and ord(ch) != 127)
    try:
        parts = urlsplit(cleaned)
    except ValueError:
        return "#"
    scheme = parts.scheme.lower()
    if scheme:
        if scheme not in _ALLOWED_SCHEMES:
            return "#"
        if not parts.netloc:
            return "#"
    else:
        # Scheme-less values: reject protocol-relative URLs and anything with a colon
        # in the first path segment that could be misparsed as a scheme.
        if cleaned.startswith("//"):
            return "#"
        first = cleaned.split("/", 1)[0]
        if ":" in first:
            return "#"
    return cleaned


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    safe_href = escape(_sanitize_url(website), quote=True)
    safe_text = escape(str(display_name), quote=True)
    return f'<a href="{safe_href}">{safe_text}</a>'
