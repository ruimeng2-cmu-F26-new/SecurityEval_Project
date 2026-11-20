import html
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = frozenset({"http", "https"})


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    url = website.strip()
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in url):
        raise ValueError("website URL contains control characters")

    scheme = urlsplit(url).scheme.lower()
    if scheme and scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"unsupported URL scheme: {scheme!r}")

    safe_href = html.escape(url, quote=True)
    safe_text = html.escape(display_name, quote=True)
    return f'<a href="{safe_href}">{safe_text}</a>'
