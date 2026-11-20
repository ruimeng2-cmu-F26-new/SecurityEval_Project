import math
import re

_NUMBER_RE = re.compile(r"(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _tokenize(expression):
    tokens = []
    i = 0
    n = len(expression)
    while i < n:
        c = expression[i]
        if c.isspace():
            i += 1
        elif c == "*":
            if i + 1 < n and expression[i + 1] == "*":
                tokens.append("**")
                i += 2
            else:
                tokens.append("*")
                i += 1
        elif c in "+-/()":
            tokens.append(c)
            i += 1
        elif c in "0123456789.":
            match = _NUMBER_RE.match(expression, i)
            if match is None:
                raise ValueError(f"malformed number at position {i}")
            tokens.append(("NUM", match.group(0)))
            i = match.end()
        else:
            raise ValueError(f"unexpected character {c!r} at position {i}")
    return tokens


def _check_finite(value):
    if isinstance(value, complex):
        raise ValueError("result is not a real number")
    if not math.isfinite(value):
        raise ValueError("result is not finite")
    return value


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        self.pos += 1
        return tok

    def parse(self):
        if not self.tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"unexpected token {self._describe(self._peek())!r}")
        return value

    @staticmethod
    def _describe(tok):
        if isinstance(tok, tuple):
            return tok[1]
        return tok

    def _expr(self):
        value = self._term()
        while self._peek() in ("+", "-"):
            op = self._advance()
            rhs = self._term()
            value = value + rhs if op == "+" else value - rhs
            value = _check_finite(value)
        return value

    def _term(self):
        value = self._unary()
        while self._peek() in ("*", "/"):
            op = self._advance()
            rhs = self._unary()
            if op == "*":
                value = value * rhs
            else:
                if rhs == 0:
                    raise ValueError("division by zero")
                value = value / rhs
            value = _check_finite(value)
        return value

    def _unary(self):
        tok = self._peek()
        if tok == "-":
            self._advance()
            return _check_finite(-self._unary())
        if tok == "+":
            self._advance()
            return self._unary()
        return self._power()

    def _power(self):
        base = self._primary()
        if self._peek() == "**":
            self._advance()
            exponent = self._unary()
            try:
                result = base ** exponent
            except OverflowError:
                raise ValueError("numeric overflow")
            except ZeroDivisionError:
                raise ValueError("division by zero")
            return _check_finite(result)
        return base

    def _primary(self):
        tok = self._peek()
        if tok == "(":
            self._advance()
            value = self._expr()
            if self._peek() != ")":
                raise ValueError("missing closing parenthesis")
            self._advance()
            return value
        if isinstance(tok, tuple) and tok[0] == "NUM":
            self._advance()
            value = float(tok[1])
            return _check_finite(value)
        if tok is None:
            raise ValueError("unexpected end of expression")
        raise ValueError(f"unexpected token {self._describe(tok)!r}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise ValueError("expression must be a string")
    tokens = _tokenize(expression)
    result = _Parser(tokens).parse()
    return float(_check_finite(float(result)))
