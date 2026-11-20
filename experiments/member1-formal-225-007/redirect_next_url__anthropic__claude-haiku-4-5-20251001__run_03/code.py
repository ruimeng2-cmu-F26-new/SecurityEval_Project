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
    
    # If next_url is a relative path (no scheme/netloc), use it directly
    if not parsed.scheme and not parsed.netloc:
        return next_url if next_url else "/"
    
    # If next_url has a scheme or netloc that doesn't match our domain, reject it
    if parsed.scheme or parsed.netloc:
        # Only allow redirects to the same domain (shop.example)
        if parsed.netloc and parsed.netloc != "shop.example":
            return "/"
        # Reconstruct path with query string for same-domain URLs
        path = parsed.path or "/"
        if parsed.query:
            return f"{path}?{parsed.query}"
        return path
    
    return "/"
