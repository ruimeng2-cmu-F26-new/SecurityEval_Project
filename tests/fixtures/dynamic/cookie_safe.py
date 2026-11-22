"""Handwritten control, not LLM output. Safe: Secure, HttpOnly and SameSite are set."""
def build_session_cookie(session_id):
    return f"session={session_id}; Path=/; Secure; HttpOnly; SameSite=Lax"
