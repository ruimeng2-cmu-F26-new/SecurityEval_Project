# HAND-WRITTEN RULE-TEST FIXTURE for AST-HASH-001 (not a SecurityEval sample or LLM output).
import hashlib
import hmac


def plain(password):
    return hashlib.sha256(password.encode()).hexdigest()  # expect: AST-HASH-001


def weak(password: str) -> str:
    data = password.encode("utf-8")
    return hashlib.md5(data).hexdigest()  # expect: AST-HASH-001


def incremental(password):
    digest = hashlib.sha512()  # expect: AST-HASH-001
    digest.update(password.encode())
    return digest.hexdigest()


def fixed_salt(password):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), b"static-salt", 100_000).hex()  # expect: AST-HASH-001


def keyed(password):
    return hmac.new(b"application-key", password.encode(), "sha256").hexdigest()  # expect: AST-HASH-001
