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

    def match_op(self, *ops):
        tok = self.peek()
        if tok is not None and tok[0] == "op" and tok[1] in ops:
            self.i += 1
            return tok[1]
        return None

    def parse(self) -> float:
        if not self.tokens:
            raise ValueError("Empty expression")
        value = self.expr()
        if self.peek() is not None:
            raise ValueError("Unexpected token")
        return value

    def expr(self) -> float:
        value = self.term()
        while True:
            op = self.match_op("+", "-")
            if op is None:
                return value
            rhs = self.term()
            value = value + rhs if op == "+" else value - rhs

    def term(self) -> float:
        value = self.unary()
        while True:
            op = self.match_op("*", "/")
            if op is None:
                return value
            rhs = self.unary()
            if op == "*":
                value = value * rhs
            else:
                try:
                    value = value / rhs
                except ZeroDivisionError:
                    raise ValueError("Division by zero")

    def unary(self) -> float:
        op = self.match_op("+", "-")
        if op is not None:
            v = self.unary()
            return -v if op == "-" else v
        return self.power()

    def power(self) -> float:
        base = self.atom()
        if self.match_op("**"):
            exp = self.unary()  # right associative, allows unary minus in exponent
            try:
                result = base ** exp
            except ZeroDivisionError:
                raise ValueError("Division by zero")
            except OverflowError:
                raise ValueError("Result too large")
            if isinstance(result, complex):
                raise ValueError("Complex result")
            return result
        return base

    def atom(self) -> float:
        tok = self.next()
        if tok[0] == "num":
            return float(tok[1])
        if tok[1] == "(":
            value = self.expr()
            if not self.match_op(")"):
                raise ValueError("Missing closing parenthesis")
            return value
        raise ValueError(f"Unexpected token {tok[1]!r}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    tokens = _tokenize(expression)
    return float(_Parser(tokens).parse())
