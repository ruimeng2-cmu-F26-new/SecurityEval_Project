# HAND-WRITTEN RULE-TEST FIXTURE for AST-URL-001 (not a SecurityEval sample or LLM output).
import re


def anchored_and_escaped(url):
    return re.fullmatch(r"https?://([a-z0-9-]+\.)*example\.com(:\d+)?(/.*)?", url) is not None  # expect: AST-URL-001
