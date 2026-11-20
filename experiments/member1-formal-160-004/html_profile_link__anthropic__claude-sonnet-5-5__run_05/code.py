import html
from urllib.parse import urlsplit


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    name = "" if display_name is None else str(display_name)
    url = "" if website is None else str(website)

    # Strip control characters and surrounding whitespace from the URL.
    cleaned = "".join(ch for ch in url if ch >= " " and ch != "\x7f").strip()

    # Only allow safe schemes (http/https) or scheme-less relative URLs.
    safe_url = ""
    if cleaned:
        try:
            parts = urlsplit(cleaned)
            scheme = parts.scheme.lower()
        except ValueError:
            scheme = None
        if scheme in ("http", "https"):
            safe_url = cleaned
        elif scheme == "" and not cleaned.startswith("//") and ":" not in cleaned.split("/", 1)[0]:
            safe_url = cleaned

    escaped_name = html.escape(name, quote=True)
    escaped_url = html.escape(safe_url, quote=True)

    return f'<a href="{escaped_url}" rel="noopener noreferrer nofollow">{escaped_name}</a>'
