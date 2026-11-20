# HAND-WRITTEN RULE-TEST FIXTURE for AST-LINK-001 (not a SecurityEval sample or LLM output).
import html


def constant_link():
    return '<a href="https://example.com/">Home</a>'


def text_only(display_name):
    return f"<span>{html.escape(display_name)}</span>"
