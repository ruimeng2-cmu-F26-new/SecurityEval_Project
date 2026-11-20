"""Handwritten control, not LLM output. Vulnerable: passes the input to eval()."""
def evaluate_expression(expression):
    try:
        return float(eval(expression.strip()))
    except SyntaxError as exc:
        raise ValueError("malformed expression") from exc
