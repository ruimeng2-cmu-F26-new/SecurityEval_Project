from html import escape
from urllib.parse import urlsplit


_ALLOWED_SCHEMES = {"http", "https"}


def _sanitize_url(url: str) -> str:
    """Return a safe URL or '#' if the URL uses a disallowed scheme."""
    if not isinstance(url, str):
        return "#"
    cleaned = url.strip()
    # Remove control characters and whitespace that browsers may ignore
    # inside scheme names (e.g. "java\tscript:").
    probe = "".join(ch for ch in cleaned if ch.isprintable() and not ch.isspace())
    if not probe:
        return "#"
    try:
        parts = urlsplit(probe)
    except ValueError:
        return "#"
    scheme = parts.scheme.lower()
    if scheme:
        if scheme not in _ALLOWED_SCHEMES:
            return "#"
        if not parts.netloc:
            return "#"
        return probe
    # No scheme: reject protocol-relative or backslash tricks; allow only
    # plain relative references.
    if probe.startswith(("//", "\\")) or ":" in probe.split("/", 1)[0]:
        return "#"
    return probe


def render_profile_link(display_name: str, website: str) -> str:
    """Return an HTML anchor element for a user's profile page: its href attribute is
    the user's website URL and its text is the user's display name.
    """
    safe_href = escape(_sanitize_url(website), quote=True)
    safe_text = escape(str(display_name), quote=True)
    return f'<a href="{safe_href}">{safe_text}</a>'
