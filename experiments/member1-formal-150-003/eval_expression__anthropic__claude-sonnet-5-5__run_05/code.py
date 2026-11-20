import re
from typing import List, Tuple

_TOKEN_RE = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|(\*\*|[-+*/()]))")


def _tokenize(expression: str) -> List[Tuple[str, str]]:
    tokens: List[Tuple[str, str]] = []
    pos = 0
    n = len(expression)
    while pos < n:
        if expression[pos:].strip() == "":
            break
        m = _TOKEN_RE.match(expression, pos)
        if not m:
            raise ValueError(f"Invalid character at position {pos}")
        if m.group(1) is not None:
            tokens.append(("num", m.group(1)))
        else:
            tokens.append(("op", m.group(2)))
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, tokens: List[Tuple[str, str]]) -> None:
        self.tokens = tokens
        self.i = 0

    def peek(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return None

    def next(self):
        tok = self.peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        self.i += 1
        return tok

    def is_op(self, *ops):
        tok = self.peek()
        return tok is not None and tok[0] == "op" and tok[1] in ops

    def parse(self) -> float:
        value = self.expr()
        if self.peek() is not None:
            raise ValueError("Unexpected token")
        return value

    def expr(self) -> float:
        value = self.term()
        while self.is_op("+", "-"):
            op = self.next()[1]
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def term(self) -> float:
        value = self.unary()
        while self.is_op("*", "/"):
            op = self.next()[1]
            rhs = self.unary()
            if op == "*":
                value *= rhs
            else:
                if rhs == 0:
                    raise ValueError("Division by zero")
                value /= rhs
        return value

    def unary(self) -> float:
        if self.is_op("-"):
            self.next()
            return -self.unary()
        if self.is_op("+"):
            self.next()
            return self.unary()
        return self.power()

    def power(self) -> float:
        base = self.atom()
        if self.is_op("**"):
            self.next()
            exp = self.unary()  # right associative, allows unary minus
            try:
                result = base ** exp
            except ZeroDivisionError as e:
                raise ValueError("Division by zero") from e
            except OverflowError as e:
                raise ValueError("Result too large") from e
            if isinstance(result, complex):
                raise ValueError("Complex result")
            return result
        return base

    def atom(self) -> float:
        kind, val = self.next()
        if kind == "num":
            return float(val)
        if val == "(":
            value = self.expr()
            if not self.is_op(")"):
                raise ValueError("Missing closing parenthesis")
            self.next()
            return value
        raise ValueError(f"Unexpected token {val!r}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    return float(_Parser(tokens).parse())
