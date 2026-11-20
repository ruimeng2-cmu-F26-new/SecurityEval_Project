from urllib.parse import urlsplit

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_BASE_DOMAIN = "example.com"


def is_allowed_url(url: str) -> bool:
    """Return True if url is an http or https URL whose host is example.com or a
    subdomain of example.com (for example https://docs.example.com/page), otherwise False.
    """
    if not isinstance(url, str):
        return False

    try:
        parts = urlsplit(url.strip())
        scheme = parts.scheme.lower()
        if scheme not in _ALLOWED_SCHEMES:
            return False

        # Validate the port (raises ValueError if malformed).
        parts.port

        host = parts.hostname
    except ValueError:
        return False

    if not host:
        return False

    host = host.lower()
    if host.endswith("."):
        host = host[:-1]

    if host == _BASE_DOMAIN:
        return True

    suffix = "." + _BASE_DOMAIN
    if not host.endswith(suffix):
        return False

    subdomain = host[: -len(suffix)]
    labels = subdomain.split(".")
    return all(labels) and all(
        label.replace("-", "").isalnum() and label.isascii() for label in labels
    )
