from urllib.parse import urlsplit

_ALLOWED_HOST = "shop.example"


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; it is returned so the user lands on that page.
    Returns "/" when next_url is empty or unsafe (e.g. points to another site).
    """
    if not next_url or not isinstance(next_url, str):
        return "/"

    candidate = next_url.strip()
    if not candidate:
        return "/"

    # Reject control characters and backslashes (browsers treat "\" like "/").
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in candidate) or "\\" in candidate:
        return "/"

    try:
        parts = urlsplit(candidate)
    except ValueError:
        return "/"

    # Absolute URL: allow only https to the shop's own host.
    if parts.scheme or parts.netloc:
        if parts.scheme.lower() != "https":
            return "/"
        try:
            host = parts.hostname
            port = parts.port
            has_creds = parts.username is not None or parts.password is not None
        except ValueError:
            return "/"
        if has_creds or host is None or host.lower() != _ALLOWED_HOST:
            return "/"
        if port not in (None, 443):
            return "/"
        path = parts.path or "/"
        if path.startswith("//"):
            return "/"
        result = path
        if parts.query:
            result += "?" + parts.query
        if parts.fragment:
            result += "#" + parts.fragment
        return result

    # Relative reference: must be an absolute path on this site, not protocol-relative.
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"

    return candidate
```
