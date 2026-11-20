import html
from urllib.parse import urlsplit


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.

    Both values are HTML-escaped. The website must use the http or https scheme,
    which prevents values such as "javascript:" URLs from becoming active links.
    """
    parsed = urlsplit(website.strip())
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        raise ValueError("website must be an absolute http or https URL")

    safe_href = html.escape(website.strip(), quote=True)
    safe_text = html.escape(display_name, quote=True)
    return f'<a href="{safe_href}">{safe_text}</a>'
