from urllib.parse import urlsplit

_SITE_HOST = "shop.example"


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    Only same-site relative paths (or absolute URLs on shop.example over
    http/https) are honored; anything else falls back to "/" to prevent
    open redirects.
    """
    if not next_url or not isinstance(next_url, str):
        return "/"

    candidate = next_url.strip()
    if not candidate:
        return "/"

    # Reject control characters and backslashes (browsers treat "\" like "/").
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in candidate) or "\\" in candidate:
        return "/"

    try:
        parts = urlsplit(candidate)
    except ValueError:
        return "/"

    if parts.scheme or parts.netloc:
        # Allow only absolute URLs pointing at this site.
        if parts.scheme not in ("http", "https"):
            return "/"
        try:
            host = parts.hostname
            port = parts.port
        except ValueError:
            return "/"
        if host is None or host.lower() != _SITE_HOST:
            return "/"
        if parts.username is not None or parts.password is not None:
            return "/"
        if port not in (None, 80, 443):
            return "/"
        path = parts.path or "/"
        result = path
        if parts.query:
            result += "?" + parts.query
        if parts.fragment:
            result += "#" + parts.fragment
        if not result.startswith("/") or result.startswith("//"):
            return "/"
        return result

    # Relative reference: must be an absolute path on this site.
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"

    return candidate
