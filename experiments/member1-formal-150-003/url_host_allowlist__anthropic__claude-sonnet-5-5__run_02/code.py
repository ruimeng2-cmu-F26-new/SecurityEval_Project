from urllib.parse import urlsplit

_ALLOWED_DOMAIN = "example.com"


def is_allowed_url(url: str) -> bool:
    """Return True if url is an http or https URL whose host is example.com or a
    subdomain of example.com (for example https://docs.example.com/page), otherwise False.
    """
    if not isinstance(url, str):
        return False
    if url != url.strip():
        return False
    # Reject control characters, whitespace and backslashes, which parsers
    # and browsers may interpret differently.
    for ch in url:
        if ord(ch) <= 0x20 or ord(ch) == 0x7F or ch == "\\":
            return False
    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        if scheme not in ("http", "https"):
            return False
        if not parts.netloc:
            return False
        # Port validation (raises ValueError if invalid)
        _ = parts.port
        host = parts.hostname
    except ValueError:
        return False
    if not host:
        return False
    # Userinfo is not allowed to avoid confusing URLs
    if "@" in parts.netloc:
        return False
    host = host.lower().rstrip(".")
    if not host:
        return False
    try:
        host.encode("ascii")
    except UnicodeEncodeError:
        return False
    if host == _ALLOWED_DOMAIN:
        return True
    if host.endswith("." + _ALLOWED_DOMAIN):
        prefix = host[: -(len(_ALLOWED_DOMAIN) + 1)]
        labels = prefix.split(".")
        return all(labels) and all(
            all(c.isalnum() or c == "-" for c in label) for label in labels
        )
    return False
