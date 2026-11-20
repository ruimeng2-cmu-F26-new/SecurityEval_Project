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

    def accept(self, op: str) -> bool:
        tok = self.peek()
        if tok is not None and tok == ("op", op):
            self.i += 1
            return True
        return False

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
            if self.accept("+"):
                value += self.term()
            elif self.accept("-"):
                value -= self.term()
            else:
                return value

    def term(self) -> float:
        value = self.unary()
        while True:
            if self.accept("*"):
                value *= self.unary()
            elif self.accept("/"):
                d = self.unary()
                if d == 0:
                    raise ValueError("Division by zero")
                value /= d
            else:
                return value

    def unary(self) -> float:
        if self.accept("-"):
            return -self.unary()
        if self.accept("+"):
            return self.unary()
        return self.power()

    def power(self) -> float:
        base = self.atom()
        if self.accept("**"):
            exp = self.unary()  # right-assoc, allows unary minus in exponent
            try:
                result = base ** exp
            except ZeroDivisionError as e:
                raise ValueError("Division by zero") from e
            except OverflowError as e:
                raise ValueError("Result too large") from e
            if isinstance(result, complex):
                raise ValueError("Complex result not supported")
            return float(result)
        return base

    def atom(self) -> float:
        kind, val = self.next()
        if kind == "num":
            return float(val)
        if val == "(":
            value = self.expr()
            if not self.accept(")"):
                raise ValueError("Missing closing parenthesis")
            return value
        raise ValueError(f"Unexpected token {val!r}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    try:
        return float(_Parser(_tokenize(expression)).parse())
    except RecursionError as e:
        raise ValueError("Expression too deeply nested") from e
    except OverflowError as e:
        raise ValueError("Numeric overflow") from e
