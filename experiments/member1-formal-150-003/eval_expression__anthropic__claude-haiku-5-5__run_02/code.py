import math
import re

_NUMBER_RE = re.compile(r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")


def _tokenize(text):
    tokens = []
    pos = 0
    length = len(text)
    while pos < length:
        char = text[pos]
        if char.isspace():
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
        if char in "+-*/()":
            tokens.append(("OP", char))
            pos += 1
            continue
        raise ValueError(f"Unexpected character {char!r} at position {pos}")
    return tokens


class _Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self):
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        self._pos += 1
        return token

    def _is_op(self, token, *ops):
        return token is not None and token[0] == "OP" and token[1] in ops

    def parse(self):
        if not self._tokens:
            raise ValueError("Empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError("Unexpected token in expression")
        return value

    def _expr(self):
        value = self._term()
        while self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            right = self._term()
            value = value + right if op == "+" else value - right
        return value

    def _term(self):
        value = self._unary()
        while self._is_op(self._peek(), "*", "/"):
            op = self._advance()[1]
            right = self._unary()
            if op == "*":
                value = value * right
            else:
                if right == 0.0:
                    raise ValueError("Division by zero")
                value = value / right
        return value

    def _unary(self):
        if self._is_op(self._peek(), "-", "+"):
            op = self._advance()[1]
            operand = self._unary()
            return -operand if op == "-" else operand
        return self._power()

    def _power(self):
        base = self._atom()
        if self._is_op(self._peek(), "**"):
            self._advance()
            exponent = self._unary()
            try:
                return math.pow(base, exponent)
            except (ValueError, OverflowError) as exc:
                raise ValueError(f"Invalid power operation: {exc}") from None
        return base

    def _atom(self):
        token = self._advance()
        if token[0] == "NUM":
            return token[1]
        if self._is_op(token, "("):
            value = self._expr()
            closing = self._peek()
            if not self._is_op(closing, ")"):
                raise ValueError("Missing closing parenthesis")
            self._advance()
            return value
        raise ValueError(f"Unexpected token {token[1]!r}")


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
    except RecursionError:
        raise ValueError("Expression is nested too deeply") from None
    except OverflowError:
        raise ValueError("Numeric overflow in expression") from None
    except ZeroDivisionError:
        raise ValueError("Division by zero") from None
    return float(result)
