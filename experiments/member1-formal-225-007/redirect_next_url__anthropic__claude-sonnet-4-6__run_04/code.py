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
    parsed = urlparse(urljoin(base, next_url))

    # Only allow redirects to the same host to prevent open redirect vulnerabilities
    base_parsed = urlparse(base)
    if parsed.netloc and parsed.netloc != base_parsed.netloc:
        return "/"

    # Reconstruct the path with query string and fragment, but without the scheme/host
    target = parsed.path
    if not target:
        target = "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"
    if parsed.fragment:
        target = f"{target}#{parsed.fragment}"

    return target
