# HAND-WRITTEN RULE-TEST FIXTURE for AST-EVAL-001 (not a SecurityEval sample or LLM output).
import ast


def literal(expression):
    return ast.literal_eval(expression)


def constant_code():
    return eval("1 + 1")


def tree_walk(expression):
    tree = ast.parse(expression, mode="eval")
    return isinstance(tree.body, ast.Constant)
