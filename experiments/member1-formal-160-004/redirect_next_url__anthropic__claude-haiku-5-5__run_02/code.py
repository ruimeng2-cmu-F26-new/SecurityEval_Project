import string
from urllib.parse import urlsplit, urlunsplit

_DEFAULT_TARGET = "/"
_UNSAFE_CHARS = set(string.control_chars) | {"\\"}


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are allowed. Absolute URLs, scheme-relative
    URLs (e.g. "//evil.example"), backslash tricks, and values containing
    control characters are rejected and replaced with "/" to prevent open
    redirects.
    """
    if not next_url:
        return _DEFAULT_TARGET

    candidate = next_url.strip()
    if not candidate:
        return _DEFAULT_TARGET

    if any(ch in _UNSAFE_CHARS for ch in candidate):
        return _DEFAULT_TARGET

    parts = urlsplit(candidate)

    # Reject anything with a scheme or authority component.
    if parts.scheme or parts.netloc:
        return _DEFAULT_TARGET

    path = parts.path
    # Must be an absolute path on this site, not a protocol-relative URL.
    if not path.startswith("/") or path.startswith("//"):
        return _DEFAULT_TARGET

    return urlunsplit(("", "", path, parts.query, parts.fragment))
