from urllib.parse import urlsplit, urlunsplit

_DEFAULT_REDIRECT = "/"


def _has_control_or_backslash(value: str) -> bool:
    for ch in value:
        if ord(ch) < 32 or ord(ch) == 127 or ch == "\\":
            return True
    return False


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if next_url is None:
        return _DEFAULT_REDIRECT

    candidate = next_url.strip()
    if not candidate:
        return _DEFAULT_REDIRECT

    if _has_control_or_backslash(candidate):
        return _DEFAULT_REDIRECT

    parts = urlsplit(candidate)

    # Reject absolute URLs (scheme present), network-location references
    # such as "//evil.example", and anything that is not a site-relative path.
    if parts.scheme or parts.netloc:
        return _DEFAULT_REDIRECT

    path = parts.path
    if not path.startswith("/") or path.startswith("//"):
        return _DEFAULT_REDIRECT

    return urlunsplit(("", "", path, parts.query, parts.fragment))
