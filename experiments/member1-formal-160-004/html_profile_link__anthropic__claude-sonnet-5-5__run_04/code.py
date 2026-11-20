import html
from urllib.parse import urlsplit


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    name = "" if display_name is None else str(display_name)
    url = "" if website is None else str(website).strip()

    safe_text = html.escape(name, quote=True)

    # Only allow safe URL schemes; otherwise neutralize the link target.
    cleaned = "".join(ch for ch in url if ord(ch) > 32 and ord(ch) != 127)
    try:
        parts = urlsplit(cleaned)
        scheme = parts.scheme.lower()
    except ValueError:
        scheme = ""
        cleaned = ""

    if scheme in ("http", "https"):
        safe_url = url
        if not parts.netloc:
            safe_url = "#"
    elif scheme == "" and cleaned and not cleaned.startswith("//"):
        # Relative URL without a scheme (e.g. "/users/1" or "example.com")
        safe_url = url
    else:
        safe_url = "#"

    safe_href = html.escape(safe_url, quote=True)
    return f'<a href="{safe_href}">{safe_text}</a>'
