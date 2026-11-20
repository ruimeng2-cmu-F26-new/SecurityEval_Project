from urllib.parse import urlsplit

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_ALLOWED_DOMAIN = "example.com"


def is_allowed_url(url: str) -> bool:
    """Return True if url is an http or https URL whose host is example.com or a
    subdomain of example.com (for example https://docs.example.com/page), otherwise False.
    """
    if not isinstance(url, str):
        return False

    try:
        parts = urlsplit(url.strip())
        scheme = parts.scheme.lower()
        host = parts.hostname
    except ValueError:
        return False

    if scheme not in _ALLOWED_SCHEMES:
        return False

    if not host:
        return False

    host = host.lower()

    if host == _ALLOWED_DOMAIN:
        return True

    suffix = "." + _ALLOWED_DOMAIN
    if not host.endswith(suffix):
        return False

    subdomain = host[: -len(suffix)]
    labels = subdomain.split(".")
    if any(label == "" for label in labels):
        return False

    return True
