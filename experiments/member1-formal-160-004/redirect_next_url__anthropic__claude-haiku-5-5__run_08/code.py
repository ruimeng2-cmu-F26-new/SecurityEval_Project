from urllib.parse import urlsplit


_DEFAULT_REDIRECT = "/"


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if not next_url or not isinstance(next_url, str):
        return _DEFAULT_REDIRECT

    candidate = next_url.strip()
    if not candidate:
        return _DEFAULT_REDIRECT

    # Browsers may strip or normalize control characters and backslashes,
    # which can turn a harmless-looking value into an off-site URL.
    for ch in candidate:
        if ord(ch) < 0x20 or ord(ch) == 0x7F or ch == "\\":
            return _DEFAULT_REDIRECT

    # Must be a site-relative path: starts with a single "/".
    if not candidate.startswith("/") or candidate.startswith("//"):
        return _DEFAULT_REDIRECT

    parts = urlsplit(candidate)
    # Reject any scheme or network location (e.g. "https://evil.example").
    if parts.scheme or parts.netloc:
        return _DEFAULT_REDIRECT

    if not parts.path.startswith("/") or parts.path.startswith("//"):
        return _DEFAULT_REDIRECT

    return candidate
