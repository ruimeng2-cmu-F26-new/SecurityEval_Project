# HAND-WRITTEN RULE-TEST FIXTURE for AST-LINK-001 (not a SecurityEval sample or LLM output).
import html
from urllib.parse import urlsplit


def parsed_scheme(display_name, website):
    if urlsplit(website).scheme not in ("http", "https"):
        raise ValueError("unsupported URL")
    return f'<a href="{html.escape(website, quote=True)}">{html.escape(display_name)}</a>'  # expect: AST-LINK-001


def prefix(display_name, website):
    href = html.escape(website, quote=True) if website.startswith(("http://", "https://")) else "#"
    return f'<a href="{href}">{html.escape(display_name)}</a>'  # expect: AST-LINK-001
