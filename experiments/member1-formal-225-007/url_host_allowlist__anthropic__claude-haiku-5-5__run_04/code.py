from urllib.parse import urlsplit

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_BASE_DOMAIN = "example.com"


def is_allowed_url(url: str) -> bool:
    """Return True if url is an http or https URL whose host is example.com or a
    subdomain of example.com (for example https://docs.example.com/page), otherwise False.
    """
    if not isinstance(url, str):
        return False

    # Reject URLs containing whitespace or control characters anywhere.
    if any(ch.isspace() or ord(ch) < 0x20 or ord(ch) == 0x7F for ch in url):
        return False

    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        host = parts.hostname
    except ValueError:
        return False

    if scheme not in _ALLOWED_SCHEMES:
        return False

    if not host:
        return False

    host = host.lower()

    # Accept a single fully-qualified trailing dot (e.g. "example.com.").
    if host.endswith("."):
        host = host[:-1]

    if not host:
        return False

    if host == _BASE_DOMAIN:
        return True

    suffix = "." + _BASE_DOMAIN
    if host.endswith(suffix):
        subdomain_part = host[: -len(suffix)]
        labels = subdomain_part.split(".")
        return all(label for label in labels)

    return False
