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
        return next_url if next_url else "/"
    
    # If next_url has a scheme or netloc, it's an absolute URL
    # Only allow redirects to the same domain (shop.example)
    if parsed.netloc and parsed.netloc != "shop.example":
        return "/"
    
    # Reconstruct the path with query string and fragment
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    if parsed.fragment:
        path += "#" + parsed.fragment
    
    return path
