"""Handwritten control, not LLM output. Safe: operating-system randomness."""
import secrets


def generate_session_id():
    return secrets.token_hex(16)
