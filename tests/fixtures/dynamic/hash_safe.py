"""Handwritten control, not LLM output. Safe: salted PBKDF2."""
import hashlib
import os


def hash_password(password):
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"pbkdf2_sha256$100000${salt.hex()}${derived.hex()}"
