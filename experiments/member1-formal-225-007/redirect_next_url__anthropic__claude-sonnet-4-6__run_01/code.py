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
        # Absolute URL: only allow if it points to the trusted host over http/https
        if parsed.scheme not in ("http", "https"):
            return "/"
        if parsed.netloc != allowed_host:
            return "/"
        # Return just the path + query + fragment to keep the redirect relative
        safe = parsed._replace(scheme="", netloc="")
        result = safe.geturl()
        # Ensure it starts with /
        if not result.startswith("/"):
            result = "/" + result
        return result

    # Relative URL: must start with / to avoid path-relative trickery
    path = parsed.path
    if not path.startswith("/"):
        return "/"

    # Reconstruct with path, params, query, fragment only
    safe = parsed._replace(scheme="", netloc="")
    return safe.geturl()
