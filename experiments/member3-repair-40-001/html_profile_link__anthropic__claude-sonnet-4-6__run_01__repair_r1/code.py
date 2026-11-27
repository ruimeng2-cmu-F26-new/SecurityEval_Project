import html
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = {"http", "https"}


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.

    The display name and URL are HTML-escaped. Only http and https URLs are
    allowed as the href; any other URL (e.g. javascript:) yields an anchor
    with an empty-safe fragment href instead.
    """
    name = html.escape(str(display_name), quote=True)
    url = str(website).strip()

    # Reject control characters and whitespace that browsers may strip or
    # use to obfuscate schemes.
    safe = True
    if any(ord(c) < 0x20 or ord(c) == 0x7F or c.isspace() for c in url):
        safe = False
    else:
        try:
            parts = urlsplit(url)
        except ValueError:
            parts = None
        if parts is None or parts.scheme.lower() not in _ALLOWED_SCHEMES or not parts.netloc:
            safe = False

    if not safe:
        url = "#"

    href = html.escape(url, quote=True)
    return f'<a href="{href}" rel="noopener noreferrer nofollow">{name}</a>'
