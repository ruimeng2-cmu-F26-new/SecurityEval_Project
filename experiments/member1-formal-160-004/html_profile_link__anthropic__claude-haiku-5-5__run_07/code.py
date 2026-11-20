import html
from urllib.parse import urlsplit

_UNSAFE_SCHEMES = frozenset({"javascript", "data", "vbscript"})


def _is_unsafe_url(url: str) -> bool:
    # Browsers ignore leading whitespace/control characters and some inner
    # whitespace/tabs/newlines when parsing schemes, so normalize before checking.
    normalized = "".join(ch for ch in url if ch.isprintable() and not ch.isspace()).lower()
    scheme = urlsplit(normalized).scheme
    return scheme in _UNSAFE_SCHEMES


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    url = str(website).strip()
    if _is_unsafe_url(url):
        raise ValueError("Unsafe URL scheme in website")

    href = html.escape(url, quote=True)
    text = html.escape(str(display_name), quote=True)
    return f'<a href="{href}">{text}</a>'
