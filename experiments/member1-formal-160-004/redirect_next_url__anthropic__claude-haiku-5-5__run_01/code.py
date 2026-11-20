import urllib.parse


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.

    Only same-site relative paths are allowed. Absolute URLs, protocol-relative
    URLs (starting with "//"), backslash tricks, and values containing control
    characters are rejected and replaced with "/" to prevent open redirects.
    """
    if not next_url or not next_url.strip():
        return "/"

    candidate = next_url.strip()

    # Browsers treat backslashes as slashes and ignore control characters,
    # so reject them outright to avoid disguised absolute/protocol-relative URLs.
    for ch in candidate:
        if ord(ch) < 32 or ord(ch) == 127 or ch == "\\":
            return "/"

    # Must be a path on this site, not a scheme-relative or absolute URL.
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"

    parts = urllib.parse.urlsplit(candidate)
    if parts.scheme or parts.netloc:
        return "/"

    return candidate
