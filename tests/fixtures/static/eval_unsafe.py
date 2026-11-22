# HAND-WRITTEN RULE-TEST FIXTURE for AST-EVAL-001 (not a SecurityEval sample or LLM output).
import builtins


def direct(expression):
    return float(eval(expression))  # expect: AST-EVAL-001


def emptied_builtins(expression):
    text = expression.strip()
    return eval(text, {"__builtins__": {}}, {})  # expect: AST-EVAL-001


def statements(code):
    exec(code)  # expect: AST-EVAL-001


def qualified(expression):
    return builtins.eval(expression)  # expect: AST-EVAL-001


def validated_by_pattern(expression):
    import re
    if not re.fullmatch(r"[0-9+*/(). -]+", expression):
        raise ValueError("bad expression")
    return eval(expression)  # expect: AST-EVAL-001
