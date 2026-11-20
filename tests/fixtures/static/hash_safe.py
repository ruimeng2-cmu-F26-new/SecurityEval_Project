# HAND-WRITTEN RULE-TEST FIXTURE for AST-HASH-001 (not a SecurityEval sample or LLM output).
import hashlib
import os
import secrets


def derived(password):
    salt = os.urandom(16)
    return salt.hex() + "$" + hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000).hex()


def memory_hard(password):
    salt = secrets.token_bytes(16)
    return salt.hex() + "$" + hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1).hex()


def constant_digest():
    return hashlib.sha256(b"fixed build label").hexdigest()
