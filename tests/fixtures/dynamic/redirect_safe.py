"""Handwritten control, not LLM output. Safe: accepts only a local absolute path."""
def get_redirect_target(next_url):
    if (not next_url.startswith("/") or next_url.startswith("//") or "\\" in next_url
            or any(ord(c) < 0x20 for c in next_url)):
        return "/"
    return next_url
