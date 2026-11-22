import math
import re

_NUMBER_RE = re.compile(r"(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _tokenize(text):
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        match = _NUMBER_RE.match(text, i)
        if match:
            tokens.append(("NUM", float(match.group())))
            i = match.end()
            continue
        if text.startswith("**", i):
            tokens.append(("OP", "**"))
            i += 2
            continue
        if ch in "+-*/()":
            tokens.append(("OP", ch))
            i += 1
            continue
        raise ValueError(f"unexpected character {ch!r} at position {i}")
    return tokens


class _Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _peek_op(self, *ops):
        tok = self._peek()
        return tok is not None and tok[0] == "OP" and tok[1] in ops

    def _advance(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def parse(self):
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._pos != len(self._tokens):
            raise ValueError("unexpected trailing input")
        return value

    def _expr(self):
        value = self._term()
        while self._peek_op("+", "-"):
            op = self._advance()[1]
            rhs = self._term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def _term(self):
        value = self._unary()
        while self._peek_op("*", "/"):
            op = self._advance()[1]
            rhs = self._unary()
            if op == "*":
                value = value * rhs
            else:
                if rhs == 0:
                    raise ValueError("division by zero")
                value = value / rhs
        return value

    def _unary(self):
        if self._peek_op("-"):
            self._advance()
            return -self._unary()
        if self._peek_op("+"):
            self._advance()
            return +self._unary()
        return self._power()

    def _power(self):
        base = self._primary()
        if self._peek_op("**"):
            self._advance()
            exponent = self._unary()
            return _power_value(base, exponent)
        return base

    def _primary(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        if tok[0] == "NUM":
            self._advance()
            return tok[1]
        if self._peek_op("("):
            self._advance()
            value = self._expr()
            if not self._peek_op(")"):
                raise ValueError("missing closing parenthesis")
            self._advance()
            return value
        raise ValueError(f"unexpected token {tok[1]!r}")


def _power_value(base, exponent):
    try:
        result = base ** exponent
    except OverflowError as exc:
        raise ValueError("numeric overflow in exponentiation") from exc
    except ZeroDivisionError as exc:
        raise ValueError("division by zero in exponentiation") from exc
    if isinstance(result, complex):
        raise ValueError("exponentiation produced a complex result")
    return result


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    try:
        tokens = _tokenize(expression)
        result = _Parser(tokens).parse()
    except RecursionError as exc:
        raise ValueError("expression is too deeply nested") from exc
    result = float(result)
    if not math.isfinite(result):
        raise ValueError("numeric overflow")
    return result
