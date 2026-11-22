# HAND-WRITTEN RULE-TEST FIXTURE for AST-REDIR-001 (not a SecurityEval sample or LLM output).
from urllib.parse import urlparse


def get_redirect_target(next_url):
    return next_url or "/"  # expect: AST-REDIR-001


def unchanged(target):
    if not target:
        return "/"
    return target  # expect: AST-REDIR-001


def leading_slash(next_url):
    return next_url if next_url.startswith("/") else "/"  # expect: AST-REDIR-001


def redirect_after_login(value):
    return value.strip()  # expect: AST-REDIR-001
