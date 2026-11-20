import re

_TOKEN_PATTERN = re.compile(
    r"""
    \s*(?:
        (?P<number>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)
      | (?P<op>\*\*|[+\-*/])
      | (?P<lparen>\()
      | (?P<rparen>\))
    )
    """,
    re.VERBOSE,
)


def _tokenize(expression: str):
    tokens = []
    pos = 0
    length = len(expression)
    while pos < length:
        if expression[pos].isspace():
            pos += 1
            continue
        match = _TOKEN_PATTERN.match(expression, pos)
        if match is None or match.end() == pos:
            raise ValueError(
                f"Invalid character {expression[pos]!r} at position {pos}"
            )
        if match.group("number") is not None:
            tokens.append(("number", float(match.group("number"))))
        elif match.group("op") is not None:
            tokens.append(("op", match.group("op")))
        elif match.group("lparen") is not None:
            tokens.append(("lparen", "("))
        elif match.group("rparen") is not None:
            tokens.append(("rparen", ")"))
        pos = match.end()
    return tokens


class _Parser:
    """
    Grammar:
        expr    := term (('+' | '-') term)*
        term    := unary (('*' | '/') unary)*
        unary   := ('-' | '+') unary | power
        power   := primary ('**' unary)?
        primary := NUMBER | '(' expr ')'
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self):
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        self.pos += 1
        return token

    def parse(self):
        if not self.tokens:
            raise ValueError("Empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token {self._peek()[1]!r}")
        return value

    def _expr(self):
        value = self._term()
        while True:
            token = self._peek()
            if token is not None and token[0] == "op" and token[1] in ("+", "-"):
                self._advance()
                right = self._term()
                value = value + right if token[1] == "+" else value - right
            else:
                return value

    def _term(self):
        value = self._unary()
        while True:
            token = self._peek()
            if token is not None and token[0] == "op" and token[1] in ("*", "/"):
                self._advance()
                right = self._unary()
                if token[1] == "*":
                    value = value * right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    value = value / right
            else:
                return value

    def _unary(self):
        token = self._peek()
        if token is not None and token[0] == "op" and token[1] in ("+", "-"):
            self._advance()
            operand = self._unary()
            return -operand if token[1] == "-" else operand
        return self._power()

    def _power(self):
        base = self._primary()
        token = self._peek()
        if token is not None and token[0] == "op" and token[1] == "**":
            self._advance()
            exponent = self._unary()
            if base == 0 and exponent < 0:
                raise ValueError("Zero cannot be raised to a negative power")
            result = base ** exponent
            if isinstance(result, complex):
                raise ValueError("Result is not a real number")
            return result
        return base

    def _primary(self):
        token = self._advance()
        if token[0] == "number":
            return token[1]
        if token[0] == "lparen":
            value = self._expr()
            closing = self._peek()
            if closing is None or closing[0] != "rparen":
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
    tokens = _tokenize(expression)
    try:
        result = _Parser(tokens).parse()
    except RecursionError as exc:
        raise ValueError("Expression is nested too deeply") from exc
    except OverflowError as exc:
        raise ValueError("Numeric overflow in expression") from exc
    except ZeroDivisionError as exc:
        raise ValueError("Division by zero") from exc
    if isinstance(result, complex):
        raise ValueError("Result is not a real number")
    return float(result)
