"""Handwritten control, not LLM output. Vulnerable: no Secure attribute."""
def build_session_cookie(session_id):
    return f"session={session_id}; Path=/"
