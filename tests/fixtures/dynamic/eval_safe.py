"""Handwritten control, not LLM output. Safe: walks the syntax tree and allows arithmetic only."""
import ast
import operator

BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
          ast.Div: operator.truediv, ast.Pow: operator.pow}


def _value(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        return BINARY[type(node.op)](_value(node.left), _value(node.right))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        value = _value(node.operand)
        return -value if isinstance(node.op, ast.USub) else value
    raise ValueError("unsupported expression")


def evaluate_expression(expression):
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError("malformed expression") from exc
    return float(_value(tree.body))
