import math
import re

_NUMBER_RE = re.compile(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_OPERATORS = ("**", "+", "-", "*", "/", "(", ")")


def _tokenize(expression):
    tokens = []
    pos = 0
    length = len(expression)
    while pos < length:
        char = expression[pos]
        if char.isspace():
            pos += 1
            continue
        match = _NUMBER_RE.match(expression, pos)
        if match:
            tokens.append(("NUM", match.group()))
            pos = match.end()
            continue
        for op in _OPERATORS:
            if expression.startswith(op, pos):
                tokens.append(("OP", op))
                pos += len(op)
                break
        else:
            raise ValueError(f"unexpected character {char!r} at position {pos}")
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
        token = self._peek()
        return token is not None and token[0] == "OP" and token[1] in ops

    def _advance(self):
        token = self._peek()
        if token is None:
            raise ValueError("unexpected end of expression")
        self._pos += 1
        return token

    def parse(self):
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"unexpected token {self._peek()[1]!r}")
        return value

    def _expr(self):
        value = self._term()
        while self._peek_op("+", "-"):
            op = self._advance()[1]
            right = self._term()
            value = value + right if op == "+" else value - right
        return value

    def _term(self):
        value = self._unary()
        while self._peek_op("*", "/"):
            op = self._advance()[1]
            right = self._unary()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                value = value / right
        return value

    def _unary(self):
        if self._peek_op("+", "-"):
            op = self._advance()[1]
            operand = self._unary()
            return -operand if op == "-" else operand
        return self._power()

    def _power(self):
        base = self._primary()
        if self._peek_op("**"):
            self._advance()
            exponent = self._unary()
            try:
                return math.pow(base, exponent)
            except (OverflowError, ValueError) as exc:
                raise ValueError(f"invalid power operation: {exc}") from None
        return base

    def _primary(self):
        token = self._peek()
        if token is None:
            raise ValueError("unexpected end of expression")
        if token[0] == "NUM":
            self._advance()
            return float(token[1])
        if token[0] == "OP" and token[1] == "(":
            self._advance()
            value = self._expr()
            if not self._peek_op(")"):
                raise ValueError("missing closing parenthesis")
            self._advance()
            return value
        raise ValueError(f"unexpected token {token[1]!r}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    tokens = _tokenize(expression)
    result = _Parser(tokens).parse()
    if not math.isfinite(result):
        raise ValueError("arithmetic result is not finite")
    return float(result)
