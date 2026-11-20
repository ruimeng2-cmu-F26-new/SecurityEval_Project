# HAND-WRITTEN RULE-TEST FIXTURE for AST-HTML-001 (not a SecurityEval sample or LLM output).
import html
from html import escape


def inline(name):
    return f"<h1>Hello, {html.escape(name)}!</h1>"


def reassigned(name):
    name = escape(name)
    return "<h1>Hello, " + name + "!</h1>"


def separate_variable(name):
    safe_name = html.escape(name, quote=True)
    return "<h1>Hello, {}!</h1>".format(safe_name)


def constant_markup():
    return "<h1>Hello!</h1>"


def not_markup(name):
    return f"Hello, {name}! 1 < 2"
