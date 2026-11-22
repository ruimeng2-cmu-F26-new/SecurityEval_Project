# HAND-WRITTEN RULE-TEST FIXTURE for AST-REDIR-001 (not a SecurityEval sample or LLM output).
PAGES = {"orders": "/orders", "account": "/account"}


def get_redirect_target(next_url):
    return PAGES.get(next_url, "/")


def is_allowed_url(url):
    return url == "https://example.com/"


def greeting(name):
    return name
