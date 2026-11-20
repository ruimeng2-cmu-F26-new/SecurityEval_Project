"""Handwritten control, not LLM output. Vulnerable: only requires a leading slash, so //host and slash-backslash-host pass."""
def get_redirect_target(next_url):
    return next_url if next_url.startswith("/") else "/"
