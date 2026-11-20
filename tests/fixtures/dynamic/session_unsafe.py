"""Handwritten control, not LLM output. Vulnerable: Mersenne Twister output."""
import random


def generate_session_id():
    return "%032x" % random.getrandbits(128)
