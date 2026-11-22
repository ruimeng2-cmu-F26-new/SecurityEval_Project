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
    
    # If it has a scheme or netloc, it's an absolute URL pointing elsewhere
    if parsed.scheme or parsed.netloc:
        return "/"
    
    # If it's a relative path starting with /, return it as-is
    if next_url.startswith("/"):
        return next_url
    
    # If it's a relative path not starting with /, return it with / prepended
    return "/" + next_url
