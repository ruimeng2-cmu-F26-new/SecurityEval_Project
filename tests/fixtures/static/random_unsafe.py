# HAND-WRITTEN RULE-TEST FIXTURE for AST-RAND-001 (not a SecurityEval sample or LLM output).
import hashlib
import random
import time
import uuid
from random import choice


def bits():
    return "%032x" % random.getrandbits(128)  # expect: AST-RAND-001


def characters():
    return "".join(choice("0123456789abcdef") for _ in range(32))  # expect: AST-RAND-001


def time_based_uuid():
    return uuid.uuid1().hex  # expect: AST-RAND-001


def hashed_clock():
    return hashlib.md5(str(time.time()).encode()).hexdigest()  # expect: AST-RAND-001
