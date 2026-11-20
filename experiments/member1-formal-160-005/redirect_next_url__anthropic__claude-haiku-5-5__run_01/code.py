from urllib.parse import urlsplit, urlunsplit

_DEFAULT_REDIRECT = "/"
_SITE_HOST = "shop.example"


def _has_unsafe_characters(value: str) -> bool:
    for ch in value:
        if ord(ch) < 0x20 or ord(ch) == 0x7F or ch.isspace():
            return True
        if ch == "\\":
            return True
    return False


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are accepted. Absolute URLs, protocol-relative
    URLs (for example "//evil.example"), backslash tricks, and values containing
    control or whitespace characters fall back to "/" to prevent open redirects.
    """
    if not next_url or not next_url.strip():
        return _DEFAULT_REDIRECT

    candidate = next_url.strip()

    if _has_unsafe_characters(candidate):
        return _DEFAULT_REDIRECT

    if not candidate.startswith("/") or candidate.startswith("//"):
        return _DEFAULT_REDIRECT

    try:
        parts = urlsplit(candidate)
    except ValueError:
        return _DEFAULT_REDIRECT

    if parts.scheme or parts.netloc:
        return _DEFAULT_REDIRECT

    path = parts.path or "/"
    if path.startswith("//"):
        return _DEFAULT_REDIRECT

    return urlunsplit(("", "", path, parts.query, parts.fragment))
