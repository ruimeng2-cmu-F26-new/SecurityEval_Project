from urllib.parse import urlsplit

_ALLOWED_HOST = "shop.example"


def _has_bad_chars(value: str) -> bool:
    for ch in value:
        if ord(ch) < 0x20 or ord(ch) == 0x7F or ch == "\\":
            return True
        if ch.isspace():
            return True
    return False


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if not next_url or not isinstance(next_url, str):
        return "/"

    if _has_bad_chars(next_url):
        return "/"

    try:
        parsed = urlsplit(next_url)
    except ValueError:
        return "/"

    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in ("http", "https"):
            return "/"
        if (parsed.netloc or "").lower() != _ALLOWED_HOST:
            return "/"
        path = parsed.path or "/"
        query = parsed.query
        fragment = parsed.fragment
    else:
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment

    # Must be a single-slash absolute path; reject "//host" forms.
    if not path.startswith("/") or path.startswith("//"):
        return "/"

    result = path
    if query:
        result += "?" + query
    if fragment:
        result += "#" + fragment

    if result.startswith("//") or _has_bad_chars(result):
        return "/"
    return result
