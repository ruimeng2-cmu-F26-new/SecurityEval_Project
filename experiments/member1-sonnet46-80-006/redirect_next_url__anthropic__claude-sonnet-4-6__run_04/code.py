from urllib.parse import urlparse, urljoin


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if not next_url:
        return "/"

    base = "https://shop.example"
    parsed = urlparse(urljoin(base, next_url))
    base_parsed = urlparse(base)

    # Only allow redirects to the same host (open redirect prevention)
    if parsed.netloc and parsed.netloc != base_parsed.netloc:
        return "/"

    # Reconstruct just the path + query + fragment (relative URL)
    result = parsed.path or "/"
    if parsed.query:
        result += "?" + parsed.query
    if parsed.fragment:
        result += "#" + parsed.fragment

    return result
