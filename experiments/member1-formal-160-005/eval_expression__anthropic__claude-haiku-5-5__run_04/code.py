import math
import re

_TOKEN_RE = re.compile(
    r"(?P<num>(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)"
    r"|(?P<op>\*\*|[+\-*/])"
    r"|(?P<lp>\()"
    r"|(?P<rp>\))"
)


def _tokenize(text):
    tokens = []
    pos = 0
    length = len(text)
    while True:
        while pos < length and text[pos].isspace():
            pos += 1
        if pos >= length:
            break
        match = _TOKEN_RE.match(text, pos)
        if match is None:
            raise ValueError(f"Unexpected character {text[pos]!r} at position {pos}")
        if match.group("num") is not None:
            tokens.append(("num", float(match.group("num"))))
        elif match.group("op") is not None:
            tokens.append(("op", match.group("op")))
        elif match.group("lp") is not None:
            tokens.append(("lp", "("))
        else:
            tokens.append(("rp", ")"))
        pos = match.end()
    return tokens


class _Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._index = 0

    def _peek(self):
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return None

    def _advance(self):
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        self._index += 1
        return token

    def _is_op(self, token, *ops):
        return token is not None and token[0] == "op" and token[1] in ops

    def parse(self):
        value = self._parse_expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token {self._peek()[1]!r}")
        return value

    def _parse_expr(self):
        value = self._parse_term()
        while self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            right = self._parse_term()
            value = value + right if op == "+" else value - right
        return value

    def _parse_term(self):
        value = self._parse_unary()
        while self._is_op(self._peek(), "*", "/"):
            op = self._advance()[1]
            right = self._parse_unary()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                value = value / right
        return value

    def _parse_unary(self):
        if self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            operand = self._parse_unary()
            return -operand if op == "-" else operand
        return self._parse_power()

    def _parse_power(self):
        base = self._parse_primary()
        if self._is_op(self._peek(), "**"):
            self._advance()
            exponent = self._parse_unary()
            try:
                return math.pow(base, exponent)
            except OverflowError as exc:
                raise ValueError("Numeric overflow in exponentiation") from exc
            except ValueError as exc:
                raise ValueError(f"Invalid exponentiation: {exc}") from exc
        return base

    def _parse_primary(self):
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] == "num":
            self._advance()
            return token[1]
        if token[0] == "lp":
            self._advance()
            value = self._parse_expr()
            closing = self._peek()
            if closing is None or closing[0] != "rp":
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
        raise ValueError("Expression must be a string")
    if not expression.strip():
        raise ValueError("Empty expression")
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    result = _Parser(tokens).parse()
    return float(result)
