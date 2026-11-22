import math
import re

__all__ = ["evaluate_expression"]

_NUMBER_RE = re.compile(r"\d+(?:\.\d*)?(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?")


def _tokenize(text: str) -> list:
    tokens = []
    pos = 0
    length = len(text)
    while pos < length:
        ch = text[pos]
        if ch.isspace():
            pos += 1
            continue
        match = _NUMBER_RE.match(text, pos)
        if match:
            tokens.append(("NUM", float(match.group())))
            pos = match.end()
            continue
        if text.startswith("**", pos):
            tokens.append(("OP", "**"))
            pos += 2
            continue
        if ch in "+-*/()":
            tokens.append(("OP", ch))
            pos += 1
            continue
        raise ValueError(f"unexpected character {ch!r} at position {pos}")
    return tokens


class _Parser:
    """Recursive-descent parser with the grammar:

        expr    := term (('+' | '-') term)*
        term    := unary (('*' | '/') unary)*
        unary   := ('+' | '-') unary | power
        power   := primary ('**' unary)?
        primary := NUMBER | '(' expr ')'
    """

    def __init__(self, tokens: list):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _match_op(self, *ops):
        tok = self._peek()
        if tok is not None and tok[0] == "OP" and tok[1] in ops:
            self._pos += 1
            return tok[1]
        return None

    def parse(self) -> float:
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"unexpected token {self._peek()[1]!r}")
        return value

    def _expr(self) -> float:
        value = self._term()
        while True:
            op = self._match_op("+", "-")
            if op is None:
                break
            rhs = self._term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def _term(self) -> float:
        value = self._unary()
        while True:
            op = self._match_op("*", "/")
            if op is None:
                break
            rhs = self._unary()
            if op == "*":
                value = value * rhs
            else:
                if rhs == 0:
                    raise ValueError("division by zero")
                value = value / rhs
        return value

    def _unary(self) -> float:
        op = self._match_op("+", "-")
        if op is not None:
            operand = self._unary()
            return -operand if op == "-" else operand
        return self._power()

    def _power(self) -> float:
        base = self._primary()
        if self._match_op("**") is not None:
            exponent = self._unary()
            return _power_op(base, exponent)
        return base

    def _primary(self) -> float:
        tok = self._peek()
        if tok is None:
            raise ValueError("unexpected end of expression")
        if tok[0] == "NUM":
            self._advance()
            return tok[1]
        if tok[0] == "OP" and tok[1] == "(":
            self._advance()
            value = self._expr()
            if self._match_op(")") is None:
                raise ValueError("missing closing parenthesis")
            return value
        raise ValueError(f"unexpected token {tok[1]!r}")


def _power_op(base: float, exponent: float) -> float:
    if base == 0 and exponent < 0:
        raise ValueError("zero cannot be raised to a negative power")
    try:
        result = base ** exponent
    except OverflowError as exc:
        raise ValueError("numeric overflow in exponentiation") from exc
    except ZeroDivisionError as exc:
        raise ValueError("zero cannot be raised to a negative power") from exc
    if isinstance(result, complex):
        raise ValueError("power would produce a complex result")
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
        raise ValueError("expression is nested too deeply") from exc
    except ZeroDivisionError as exc:
        raise ValueError("division by zero") from exc
    if not math.isfinite(result):
        raise ValueError("result is not a finite number")
    return float(result)
