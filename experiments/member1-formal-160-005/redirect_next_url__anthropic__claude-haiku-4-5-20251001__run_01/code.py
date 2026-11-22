def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    from urllib.parse import urlparse
    
    if not next_url:
        return "/"
    
    # Parse the URL to validate it
    parsed = urlparse(next_url)
    
    # If next_url is a relative URL (no scheme and no netloc), use it as-is
    if not parsed.scheme and not parsed.netloc:
        # Ensure it starts with / for relative paths
        if next_url and not next_url.startswith('/'):
            return "/" + next_url
        return next_url
    
    # If next_url is an absolute URL with a different host, reject it for security
    # Only allow relative URLs for safety (open redirect prevention)
    return "/"
