from urllib.parse import urlparse


def is_allowed_url(url: str) -> bool:
    """Return True if url is an http or https URL whose host is example.com or a
    subdomain of example.com (for example https://docs.example.com/page), otherwise False.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    
    # Check scheme is http or https
    if parsed.scheme not in ('http', 'https'):
        return False
    
    # Get the hostname
    hostname = parsed.hostname
    if not hostname:
        return False
    
    # Check if hostname is example.com or a subdomain of example.com
    hostname_lower = hostname.lower()
    
    if hostname_lower == 'example.com':
        return True
    
    if hostname_lower.endswith('.example.com'):
        return True
    
    return False
