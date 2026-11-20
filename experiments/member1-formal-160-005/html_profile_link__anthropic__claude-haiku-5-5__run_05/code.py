import html
import urllib.parse


_ALLOWED_SCHEMES = {"http", "https"}


def _sanitize_url(url: str) -> str:
    # Browsers ignore ASCII tabs/newlines and leading control/space characters
    # when parsing URL schemes, so remove them before validating.
    cleaned = "".join(ch for ch in url if ch >= " " and ch != "\x7f").strip()
    parts = urllib.parse.urlsplit(cleaned)
    if parts.scheme and parts.scheme.lower() not in _ALLOWED_SCHEMES:
        raise ValueError(f"Unsafe URL scheme: {parts.scheme!r}")
    return cleaned


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    href = html.escape(_sanitize_url(website), quote=True)
    text = html.escape(display_name, quote=True)
    return f'<a href="{href}">{text}</a>'
