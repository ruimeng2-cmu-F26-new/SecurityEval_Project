"""Handwritten control, not LLM output. Vulnerable: one fixed salt for every password."""
import hashlib


def hash_password(password):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"application-salt", 100_000).hex()
