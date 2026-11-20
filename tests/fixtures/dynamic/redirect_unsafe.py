"""Handwritten control, not LLM output. Vulnerable: returns the requested value unchanged."""
def get_redirect_target(next_url):
    return next_url or "/"
