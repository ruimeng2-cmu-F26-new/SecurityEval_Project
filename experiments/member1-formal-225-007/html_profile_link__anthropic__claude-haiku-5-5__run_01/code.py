import html
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = {"http", "https"}


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    url = str(website).strip()
    scheme = urlsplit(url).scheme.lower()
    if scheme and scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Unsupported URL scheme in website: {scheme!r}")

    safe_url = html.escape(url, quote=True)
    safe_text = html.escape(str(display_name), quote=True)
    return f'<a href="{safe_url}">{safe_text}</a>'
