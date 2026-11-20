from urllib.parse import urlparse, urljoin


def get_redirect_target(next_url: str) -> str:
    """Return the location to redirect a user to after login on https://shop.example.
    next_url is the page the user originally requested on this site, such as
    "/orders/42?tab=items"; return it so the user lands on that page.
    Return "/" when next_url is empty.
    """
    if not next_url or not next_url.strip():
        return "/"

    base = "https://shop.example"

    # Resolve the URL relative to the base to handle relative paths
    resolved = urljoin(base, next_url)
    parsed = urlparse(resolved)

    # Ensure the resolved URL belongs to the same host (open redirect prevention)
    base_parsed = urlparse(base)
    if parsed.netloc and parsed.netloc != base_parsed.netloc:
        return "/"

    # Reconstruct just the path + query + fragment (no scheme/host)
    result = parsed.path
    if not result:
        result = "/"
    if parsed.query:
        result = f"{result}?{parsed.query}"
    if parsed.fragment:
        result = f"{result}#{parsed.fragment}"

    return result
