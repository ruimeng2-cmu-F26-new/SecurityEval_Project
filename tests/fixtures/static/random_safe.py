# HAND-WRITTEN RULE-TEST FIXTURE for AST-RAND-001 (not a SecurityEval sample or LLM output).
import hashlib
import os
import secrets
import time
import uuid


def token():
    return secrets.token_hex(16)


def urandom():
    return os.urandom(16).hex()


def random_uuid():
    return uuid.uuid4().hex


def clock_mixed_with_entropy():
    return hashlib.sha256(os.urandom(32) + str(time.time()).encode()).hexdigest()[:32]


def elapsed(start):
    return time.time() - start
