from urllib.parse import urlsplit

_SITE_HOST = "shop.example"


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.

    Only local paths (or absolute URLs pointing at shop.example) are allowed;
    anything else falls back to "/".
    """
    if not next_url or not isinstance(next_url, str):
        return "/"

    candidate = next_url.strip()
    if not candidate:
        return "/"

    # Reject control characters and backslashes (browsers treat "\" like "/").
    if any(ord(c) < 32 or ord(c) == 127 for c in candidate) or "\\" in candidate:
        return "/"

    try:
        parts = urlsplit(candidate)
    except ValueError:
        return "/"

    if parts.scheme or parts.netloc:
        # Allow only absolute https URLs to this exact site; convert to a path.
        if parts.scheme == "https" and parts.netloc.lower() in (
            _SITE_HOST,
            _SITE_HOST + ":443",
        ) and "@" not in parts.netloc:
            path = parts.path or "/"
            if not path.startswith("/"):
                path = "/" + path
            if path.startswith("//"):
                return "/"
            result = path
            if parts.query:
                result += "?" + parts.query
            if parts.fragment:
                result += "#" + parts.fragment
            return result
        return "/"

    # Relative reference: must be an absolute path on this site, not protocol-relative.
    if not candidate.startswith("/") or candidate.startswith("//"):
        return "/"

    return candidate
