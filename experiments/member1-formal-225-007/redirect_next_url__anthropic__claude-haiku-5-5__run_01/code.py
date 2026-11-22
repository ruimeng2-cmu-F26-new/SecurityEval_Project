from urllib.parse import urlsplit, urlunsplit

_DEFAULT_REDIRECT = "/"


def _has_unsafe_characters(value: str) -> bool:
    for ch in value:
        if ord(ch) < 0x20 or ord(ch) == 0x7F or ch == "\\":
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

    if _has_unsafe_characters(candidate):
        return _DEFAULT_REDIRECT

    # Must be a site-relative path: a single leading slash, never "//" or "/\"
    # (protocol-relative URLs that would leave this site).
    if not candidate.startswith("/"):
        return _DEFAULT_REDIRECT
    if len(candidate) > 1 and candidate[1] in ("/", "\\"):
        return _DEFAULT_REDIRECT

    parts = urlsplit(candidate)

    # Reject any absolute URL or URL carrying its own host/scheme.
    if parts.scheme or parts.netloc:
        return _DEFAULT_REDIRECT

    path = parts.path or "/"
    if not path.startswith("/"):
        return _DEFAULT_REDIRECT

    return urlunsplit(("", "", path, parts.query, parts.fragment))
