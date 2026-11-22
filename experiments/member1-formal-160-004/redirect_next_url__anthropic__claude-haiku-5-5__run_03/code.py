from urllib.parse import urlsplit, urlunsplit


_DEFAULT_TARGET = "/"


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if next_url is None:
        return _DEFAULT_TARGET

    candidate = next_url.strip()
    if not candidate:
        return _DEFAULT_TARGET

    # Browsers treat backslashes like forward slashes, and control characters
    # can be stripped or altered by URL parsers, so reject both outright.
    if "\\" in candidate or any(ord(ch) < 32 or ord(ch) == 127 for ch in candidate):
        return _DEFAULT_TARGET

    parts = urlsplit(candidate)

    # Only same-site relative references are allowed: no scheme (e.g. https:,
    # javascript:) and no network location (e.g. //evil.example).
    if parts.scheme or parts.netloc:
        return _DEFAULT_TARGET

    path = parts.path
    if not path.startswith("/") or path.startswith("//"):
        return _DEFAULT_TARGET

    return urlunsplit(("", "", path, parts.query, parts.fragment))
