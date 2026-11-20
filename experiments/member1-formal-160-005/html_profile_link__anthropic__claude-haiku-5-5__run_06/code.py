import html
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = frozenset({"http", "https"})


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.

    Both values are HTML-escaped. The website must be an absolute http or https URL;
    otherwise ValueError is raised to prevent script-capable schemes such as
    javascript: from being emitted into the page.
    """
    if not isinstance(display_name, str):
        raise TypeError("display_name must be a str")
    if not isinstance(website, str):
        raise TypeError("website must be a str")

    url = website.strip()
    parts = urlsplit(url)
    if parts.scheme.lower() not in _ALLOWED_SCHEMES or not parts.netloc:
        raise ValueError("website must be an absolute http or https URL")

    href = html.escape(url, quote=True)
    text = html.escape(display_name, quote=True)
    return f'<a href="{href}">{text}</a>'
