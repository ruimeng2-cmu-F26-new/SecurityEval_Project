import re

_NUMBER_RE = re.compile(r"(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_OPERATORS = ("**", "+", "-", "*", "/", "(", ")")


def _tokenize(expression: str) -> list:
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
            tokens.append(("NUM", float(match.group(0))))
            pos = match.end()
            continue
        for op in _OPERATORS:
            if expression.startswith(op, pos):
                tokens.append(("OP", op))
                pos += len(op)
                break
        else:
            raise ValueError(f"Invalid character {char!r} at position {pos}")
    return tokens


class _Parser:
    def __init__(self, tokens: list):
        self._tokens = tokens
        self._index = 0

    def _peek_op(self):
        if self._index < len(self._tokens):
            kind, value = self._tokens[self._index]
            if kind == "OP":
                return value
        return None

    def _advance(self):
        token = self._tokens[self._index]
        self._index += 1
        return token

    def parse(self) -> float:
        if not self._tokens:
            raise ValueError("Empty expression")
        value = self._expr()
        if self._index != len(self._tokens):
            raise ValueError("Unexpected token at end of expression")
        return value

    def _expr(self) -> float:
        value = self._term()
        while self._peek_op() in ("+", "-"):
            op = self._advance()[1]
            right = self._term()
            value = value + right if op == "+" else value - right
        return value

    def _term(self) -> float:
        value = self._unary()
        while self._peek_op() in ("*", "/"):
            op = self._advance()[1]
            right = self._unary()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                value = value / right
        return value

    def _unary(self) -> float:
        if self._peek_op() in ("+", "-"):
            op = self._advance()[1]
            operand = self._unary()
            return -operand if op == "-" else operand
        return self._power()

    def _power(self) -> float:
        base = self._primary()
        if self._peek_op() == "**":
            self._advance()
            exponent = self._unary()
            return _checked_power(base, exponent)
        return base

    def _primary(self) -> float:
        if self._index >= len(self._tokens):
            raise ValueError("Unexpected end of expression")
        kind, value = self._advance()
        if kind == "NUM":
            return value
        if value == "(":
            inner = self._expr()
            if self._peek_op() != ")":
                raise ValueError("Missing closing parenthesis")
            self._advance()
            return inner
        raise ValueError(f"Unexpected operator {value!r}")


def _checked_power(base: float, exponent: float) -> float:
    try:
        result = base ** exponent
    except ZeroDivisionError:
        raise ValueError("Division by zero in exponentiation")
    except OverflowError:
        raise ValueError("Numeric overflow in exponentiation")
    if isinstance(result, complex):
        raise ValueError("Exponentiation produced a complex result")
    return result


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    if not expression.strip():
        raise ValueError("Empty expression")
    try:
        tokens = _tokenize(expression)
        result = _Parser(tokens).parse()
    except RecursionError:
        raise ValueError("Expression is nested too deeply")
    except OverflowError:
        raise ValueError("Numeric overflow in expression")
    return float(result)
