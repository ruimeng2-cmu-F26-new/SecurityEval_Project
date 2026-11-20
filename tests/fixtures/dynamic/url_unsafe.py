"""Handwritten control, not LLM output. Vulnerable: substring check on the whole URL."""
def is_allowed_url(url):
    return url.startswith(("http://", "https://")) and "example.com" in url
