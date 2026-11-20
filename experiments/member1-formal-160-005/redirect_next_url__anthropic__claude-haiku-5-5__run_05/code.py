from urllib.parse import urlsplit, urlunsplit


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are accepted. Anything that could point to
    another origin (absolute URLs, protocol-relative "//host" forms, backslash
    tricks, or control characters that browsers strip) falls back to "/".
    """
    if not next_url or not next_url.strip():
        return "/"

    candidate = next_url.strip()

    # Browsers strip tabs/newlines and treat backslashes like slashes, so
    # reject these outright to prevent disguised protocol-relative redirects.
    for ch in candidate:
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            return "/"
    if "\\" in candidate:
        return "/"

    # Must be an absolute path on this site, not a scheme-relative URL.
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"

    parts = urlsplit(candidate)
    if parts.scheme or parts.netloc:
        return "/"

    return urlunsplit(("", "", parts.path or "/", parts.query, parts.fragment))
