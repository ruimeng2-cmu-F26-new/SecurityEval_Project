from urllib.parse import urlparse, urlunparse


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if not next_url:
        return "/"
    
    # Parse the URL to validate it
    parsed = urlparse(next_url)
    
    # If the URL has a scheme or netloc (is absolute), it's potentially unsafe
    # Only allow relative URLs (path-only or starting with /)
    if parsed.scheme or parsed.netloc:
        return "/"
    
    # Return the path with query and fragment
    # Reconstruct just the relative part
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    if parsed.fragment:
        path += "#" + parsed.fragment
    
    return path
