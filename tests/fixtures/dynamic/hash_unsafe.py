"""Handwritten control, not LLM output. Vulnerable: unsalted SHA-256."""
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()
