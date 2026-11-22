import re
from urllib.parse import urlsplit, urlunsplit

_UNSAFE_CHARS_RE = re.compile(r"[\x00-\x20\x7f]")
_DEFAULT_TARGET = "/"


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are honored. Absolute URLs, protocol-relative
    URLs ("//host/..."), URLs with schemes (e.g. "javascript:"), backslash
    tricks, and values containing control characters or whitespace are
    rejected and replaced with "/" to prevent open redirects.
    """
    if not isinstance(next_url, str) or not next_url:
        return _DEFAULT_TARGET

    if _UNSAFE_CHARS_RE.search(next_url) or "\\" in next_url:
        return _DEFAULT_TARGET

    try:
        parts = urlsplit(next_url)
    except ValueError:
        return _DEFAULT_TARGET

    if parts.scheme or parts.netloc:
        return _DEFAULT_TARGET

    path = parts.path
    if not path.startswith("/") or path.startswith("//"):
        return _DEFAULT_TARGET

    return urlunsplit(("", "", path, parts.query, parts.fragment))
