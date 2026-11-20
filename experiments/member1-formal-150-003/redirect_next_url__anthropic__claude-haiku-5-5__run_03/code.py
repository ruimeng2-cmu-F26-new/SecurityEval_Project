from urllib.parse import urlsplit

_DEFAULT_REDIRECT = "/"


def _has_unsafe_characters(value: str) -> bool:
    for ch in value:
        if ch == "\\" or ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F:
            return True
    return False


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are accepted. Absolute URLs, protocol-relative
    URLs (e.g. "//evil.example"), backslash or control-character tricks, and
    anything else that could leave the site cause a fallback to "/".
    """
    if next_url is None:
        return _DEFAULT_REDIRECT

    candidate = next_url.strip()
    if not candidate:
        return _DEFAULT_REDIRECT

    if _has_unsafe_characters(candidate):
        return _DEFAULT_REDIRECT

    try:
        parts = urlsplit(candidate)
    except ValueError:
        return _DEFAULT_REDIRECT

    # Reject any scheme or network location (absolute or protocol-relative URLs).
    if parts.scheme or parts.netloc:
        return _DEFAULT_REDIRECT

    path = parts.path
    if not path.startswith("/") or path.startswith("//"):
        return _DEFAULT_REDIRECT

    return candidate
