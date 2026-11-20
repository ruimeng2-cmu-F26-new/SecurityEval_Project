import html
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = frozenset({"http", "https"})


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.

    Both values are HTML-escaped so they cannot break out of the element or
    attribute. The website must be an absolute http or https URL; any other
    scheme (for example "javascript:") raises ValueError.
    """
    url = str(website).strip()
    scheme = urlsplit(url).scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Unsupported or missing URL scheme in website: {website!r}")

    href = html.escape(url, quote=True)
    text = html.escape(str(display_name), quote=True)
    return f'<a href="{href}">{text}</a>'
