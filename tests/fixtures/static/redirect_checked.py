# HAND-WRITTEN RULE-TEST FIXTURE for AST-REDIR-001 (not a SecurityEval sample or LLM output).
from urllib.parse import urlparse


def parsed(next_url):
    parts = urlparse(next_url)
    if parts.netloc or parts.scheme:
        return "/"
    return next_url  # expect: AST-REDIR-001


def local_path(next_url):
    if not next_url.startswith("/") or next_url.startswith("//") or "\\" in next_url:
        return "/"
    return next_url  # expect: AST-REDIR-001
