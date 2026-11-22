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
    
    # If next_url is a relative path (no scheme/netloc), return it as-is
    if not parsed.scheme and not parsed.netloc:
        # Ensure it starts with / for relative paths
        if next_url.startswith("/"):
            return next_url
        else:
            return "/" + next_url
    
    # If it has a scheme or netloc, it's an absolute URL
    # Only allow redirects to the same domain (shop.example)
    if parsed.netloc and parsed.netloc not in ("shop.example", "www.shop.example"):
        return "/"
    
    # Return the path with query string if it's on the allowed domain
    path = parsed.path or "/"
    if parsed.query:
        return f"{path}?{parsed.query}"
    if parsed.fragment:
        return f"{path}#{parsed.fragment}"
    return path
