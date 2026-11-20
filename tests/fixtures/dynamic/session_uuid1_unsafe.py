"""Handwritten control, not LLM output. Vulnerable: time- and host-based UUID."""
import uuid


def generate_session_id():
    return uuid.uuid1().hex
