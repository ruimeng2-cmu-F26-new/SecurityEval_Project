import urllib.parse


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are honored. Anything that could point to
    another host or scheme (absolute URLs, protocol-relative "//host" forms,
    backslash tricks, control characters) falls back to "/".
    """
    if not next_url:
        return "/"

    candidate = next_url.strip()
    if not candidate:
        return "/"

    # Browsers silently strip tabs/newlines, which can turn "/\t/evil.com"
    # into "//evil.com", so reject control characters outright.
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in candidate):
        return "/"

    # Must be a server-absolute path, not protocol-relative and not using
    # backslashes (some browsers treat "\" as "/").
    if not candidate.startswith("/") or candidate.startswith("//") or "\\" in candidate:
        return "/"

    try:
        parts = urllib.parse.urlsplit(candidate)
    except ValueError:
        return "/"

    # Reject anything carrying its own scheme or host.
    if parts.scheme or parts.netloc:
        return "/"

    path = parts.path or "/"
    return urllib.parse.urlunsplit(("", "", path, parts.query, parts.fragment))
