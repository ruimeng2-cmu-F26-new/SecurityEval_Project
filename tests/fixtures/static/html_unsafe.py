# HAND-WRITTEN RULE-TEST FIXTURE for AST-HTML-001 (not a SecurityEval sample or LLM output).
def formatted(name):
    return f"<h1>Hello, {name}!</h1>"  # expect: AST-HTML-001


def concatenated(name):
    return "<h1>Hello, " + name + "!</h1>"  # expect: AST-HTML-001


def percent_style(name):
    return "<h1>Hello, %s!</h1>" % name  # expect: AST-HTML-001


def format_method(name):
    return "<h1>Hello, {}!</h1>".format(name)  # expect: AST-HTML-001


def through_variable(name):
    display = name.strip()
    page = f"<div><h1>Hello, {display}!</h1></div>"  # expect: AST-HTML-001
    return page


def hand_written(name):
    cleaned = name.replace("<", "&lt;")
    return f"<h1>Hello, {cleaned}!</h1>"  # expect: AST-HTML-001
