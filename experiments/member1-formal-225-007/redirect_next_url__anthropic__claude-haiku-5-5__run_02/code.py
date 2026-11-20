from urllib.parse import urlsplit, urlunsplit

_SITE_HOST = "shop.example"
_DEFAULT_TARGET = "/"


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

    Any value that would send the user off-site or is otherwise unsafe to
    redirect to (other hosts, protocol-relative URLs, non-HTTP schemes,
    control characters, malformed input) falls back to "/".
    """
    if next_url is None:
        return _DEFAULT_TARGET

    candidate = next_url.strip()
    if not candidate:
        return _DEFAULT_TARGET

    if _has_unsafe_characters(candidate):
        return _DEFAULT_TARGET

    try:
        parts = urlsplit(candidate)
        # Accessing .hostname/.port can raise ValueError on malformed netlocs.
        hostname = parts.hostname
        port = parts.port
    except ValueError:
        return _DEFAULT_TARGET

    if parts.scheme or parts.netloc:
        # Absolute URL: only accept plain http(s) to this exact site.
        if parts.scheme.lower() not in ("http", "https"):
            return _DEFAULT_TARGET
        if hostname != _SITE_HOST or port is not None:
            return _DEFAULT_TARGET
        if "@" in parts.netloc:
            return _DEFAULT_TARGET
    else:
        # Relative reference: must be an absolute path on this site.
        if not candidate.startswith("/"):
            return _DEFAULT_TARGET

    path = parts.path or "/"
    if not path.startswith("/"):
        return _DEFAULT_TARGET

    result = urlunsplit(("", "", path, parts.query, parts.fragment))

    # Final guard against protocol-relative or backslash-based redirects.
    if not result.startswith("/") or result.startswith("//") or result.startswith("/\\"):
        return _DEFAULT_TARGET

    return result
