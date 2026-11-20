from urllib.parse import urlparse


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if not next_url:
        return "/"

    parsed = urlparse(next_url)

    # Allow only relative URLs (no scheme, no netloc) or URLs that explicitly
    # target the same host to prevent open-redirect vulnerabilities.
    allowed_host = "shop.example"

    if parsed.scheme or parsed.netloc:
        # Absolute URL: only allow if it points to our own host.
        if parsed.netloc != allowed_host:
            return "/"
        # Return only the path + query + fragment portion.
        safe = parsed.path or "/"
        if parsed.query:
            safe += "?" + parsed.query
        if parsed.fragment:
            safe += "#" + parsed.fragment
        return safe

    # Relative URL: ensure it starts with "/" to avoid protocol-relative tricks
    # or paths that could be misinterpreted by the browser.
    path = parsed.path
    if not path.startswith("/"):
        return "/"

    safe = path
    if parsed.query:
        safe += "?" + parsed.query
    if parsed.fragment:
        safe += "#" + parsed.fragment
    return safe
