import html
from urllib.parse import urlsplit


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    name = "" if display_name is None else str(display_name)
    url = "" if website is None else str(website).strip()

    safe_text = html.escape(name, quote=True)

    # Only allow http/https absolute URLs; otherwise neutralize the link target.
    allowed = False
    try:
        # Reject control characters / whitespace within the URL
        if url and not any(ord(c) < 32 or ord(c) == 127 or c.isspace() for c in url):
            parts = urlsplit(url)
            if parts.scheme.lower() in ("http", "https") and parts.netloc:
                allowed = True
    except ValueError:
        allowed = False

    href = html.escape(url, quote=True) if allowed else "#"
    if allowed:
        return f'<a href="{href}" rel="noopener noreferrer nofollow">{safe_text}</a>'
    return f'<a href="{href}">{safe_text}</a>'
