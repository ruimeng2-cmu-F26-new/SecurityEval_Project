import re

_NUMBER_RE = re.compile(r'(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?')


def _tokenize(expression: str) -> list:
    tokens = []
    i = 0
    n = len(expression)
    while i < n:
        ch = expression[i]
        if ch.isspace():
            i += 1
            continue
        match = _NUMBER_RE.match(expression, i)
        if match:
            tokens.append(("NUM", float(match.group())))
            i = match.end()
            continue
        if expression.startswith("**", i):
            tokens.append(("OP", "**"))
            i += 2
            continue
        if ch in "+-*/()":
            tokens.append(("OP", ch))
            i += 1
            continue
        raise ValueError(f"Unexpected character {ch!r} at position {i}")
    return tokens


class _Parser:
    def __init__(self, tokens: list):
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

    def _match_op(self, *ops) -> str | None:
        token = self._peek()
        if token is not None and token[0] == "OP" and token[1] in ops:
            self._pos += 1
            return token[1]
        return None

    def parse(self) -> float:
        if not self._tokens:
            raise ValueError("Empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError("Unexpected token in expression")
        return value

    # expr := term (('+' | '-') term)*
    def _expr(self) -> float:
        value = self._term()
        while True:
            op = self._match_op("+", "-")
            if op is None:
                break
            right = self._term()
            value = value + right if op == "+" else value - right
        return value

    # term := unary (('*' | '/') unary)*
    def _term(self) -> float:
        value = self._unary()
        while True:
            op = self._match_op("*", "/")
            if op is None:
                break
            right = self._unary()
            if op == "*":
                value = value * right
            else:
                value = value / right
        return value

    # unary := ('+' | '-') unary | power
    def _unary(self) -> float:
        op = self._match_op("+", "-")
        if op is not None:
            operand = self._unary()
            return -operand if op == "-" else operand
        return self._power()

    # power := atom ('**' unary)?   (right-associative, exponent may be signed)
    def _power(self) -> float:
        base = self._atom()
        if self._match_op("**") is not None:
            exponent = self._unary()
            result = base ** exponent
            if isinstance(result, complex):
                raise ValueError("Result is not a real number")
            return result
        return base

    # atom := NUMBER | '(' expr ')'
    def _atom(self) -> float:
        token = self._advance()
        if token[0] == "NUM":
            return token[1]
        if token == ("OP", "("):
            value = self._expr()
            closing = self._peek()
            if closing != ("OP", ")"):
                raise ValueError("Missing closing parenthesis")
            self._pos += 1
            return value
        raise ValueError(f"Unexpected token {token[1]!r}")


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    tokens = _tokenize(expression)
    result = _Parser(tokens).parse()
    return float(result)
