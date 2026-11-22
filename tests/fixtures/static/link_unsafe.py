# HAND-WRITTEN RULE-TEST FIXTURE for AST-LINK-001 (not a SecurityEval sample or LLM output).
import html


def formatted(display_name, website):
    return f'<a href="{website}">{display_name}</a>'  # expect: AST-LINK-001 AST-HTML-001


def escaped_only(display_name, website):
    return f'<a href="{html.escape(website, quote=True)}">{html.escape(display_name)}</a>'  # expect: AST-LINK-001


def escaped_variables(display_name, website):
    href = html.escape(website, quote=True)
    text = html.escape(display_name)
    return '<a href="' + href + '">' + text + "</a>"  # expect: AST-LINK-001
