"""Handwritten control, not LLM output. Safe: default verifying context."""
import ssl


def get_ssl_context():
    return ssl.create_default_context()
