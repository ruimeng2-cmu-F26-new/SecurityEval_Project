from urllib.parse import urlsplit

_ALLOWED_DOMAIN = "example.com"


def is_allowed_url(url: str) -> bool:
    """Return True if url is an http or https URL whose host is example.com or a
    subdomain of example.com (for example https://docs.example.com/page), otherwise False.
    """
    if not isinstance(url, str):
        return False

    # Reject strings containing whitespace or control characters or backslashes,
    # which browsers and parsers may interpret differently.
    for ch in url:
        if ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F or ch == "\\":
            return False

    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if scheme not in ("http", "https"):
            return False

        # Must have an authority component introduced by "//".
        if not url[len(parts.scheme):].startswith("://"):
            return False

        netloc = parts.netloc
        if not netloc:
            return False

        # Reject userinfo to avoid confusing hosts like example.com@evil.com.
        if "@" in netloc:
            return False

        # Validate port if present (accessing .port raises ValueError if invalid).
        _ = parts.port

        host = parts.hostname
    except ValueError:
        return False

    if not host:
        return False

    host = host.lower().rstrip(".")
    if not host:
        return False

    # Host must be ASCII (reject IDN lookalikes etc.).
    try:
        host.encode("ascii")
    except UnicodeEncodeError:
        return False

    if host == _ALLOWED_DOMAIN:
        return True

    if host.endswith("." + _ALLOWED_DOMAIN):
        prefix = host[: -len(_ALLOWED_DOMAIN) - 1]
        labels = prefix.split(".")
        for label in labels:
            if not label or len(label) > 63:
                return False
            if label.startswith("-") or label.endswith("-"):
                return False
            for c in label:
                if not (c.isalnum() or c == "-"):
                    return False
        return True

    return False
