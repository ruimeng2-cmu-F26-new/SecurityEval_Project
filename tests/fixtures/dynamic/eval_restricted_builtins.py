"""Handwritten control, not LLM output. Vulnerable: eval() with emptied builtins is still escapable through object subclasses."""
def evaluate_expression(expression):
    try:
        return float(eval(expression.strip(), {"__builtins__": {}}, {}))
    except SyntaxError as exc:
        raise ValueError("malformed expression") from exc
