import re

_TOKEN_RE = re.compile(
    r"\s*(?:"
    r"(?P<NUMBER>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
    r"|(?P<OP>\*\*|[+\-*/])"
    r"|(?P<LPAREN>\()"
    r"|(?P<RPAREN>\))"
    r")"
)


def _tokenize(expression: str) -> list:
    tokens = []
    pos = 0
    length = len(expression)
    while pos < length:
        if expression[pos].isspace():
            pos += 1
            continue
        match = _TOKEN_RE.match(expression, pos)
        if not match or match.end() == pos:
            raise ValueError(f"Invalid character at position {pos}: {expression[pos]!r}")
        kind = match.lastgroup
        tokens.append((kind, match.group(kind)))
        pos = match.end()
    return tokens


class _Parser:
    # Grammar:
    #   expr   := term (('+' | '-') term)*
    #   term   := factor (('*' | '/') factor)*
    #   factor := ('+' | '-') factor | power
    #   power  := atom ('**' factor)?          (right-associative)
    #   atom   := NUMBER | '(' expr ')'

    def __init__(self, tokens: list):
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

    def parse(self) -> float:
        if not self.tokens:
            raise ValueError("Empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token {self._peek()[1]!r}")
        return value

    def _expr(self) -> float:
        value = self._term()
        while True:
            token = self._peek()
            if token is not None and token[0] == "OP" and token[1] in ("+", "-"):
                self._advance()
                right = self._term()
                value = value + right if token[1] == "+" else value - right
            else:
                return value

    def _term(self) -> float:
        value = self._factor()
        while True:
            token = self._peek()
            if token is not None and token[0] == "OP" and token[1] in ("*", "/"):
                self._advance()
                right = self._factor()
                if token[1] == "*":
                    value = value * right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    value = value / right
            else:
                return value

    def _factor(self) -> float:
        token = self._peek()
        if token is not None and token[0] == "OP" and token[1] in ("+", "-"):
            self._advance()
            operand = self._factor()
            return -operand if token[1] == "-" else operand
        return self._power()

    def _power(self) -> float:
        base = self._atom()
        token = self._peek()
        if token is not None and token[0] == "OP" and token[1] == "**":
            self._advance()
            exponent = self._factor()
            try:
                result = base ** exponent
            except ZeroDivisionError:
                raise ValueError("Division by zero")
            except OverflowError:
                raise ValueError("Numeric overflow")
            if isinstance(result, complex):
                raise ValueError("Result is not a real number")
            return result
        return base

    def _atom(self) -> float:
        token = self._advance()
        kind, text = token
        if kind == "NUMBER":
            try:
                return float(text)
            except ValueError:
                raise ValueError(f"Malformed number {text!r}")
        if kind == "LPAREN":
            value = self._expr()
            closing = self._peek()
            if closing is None or closing[0] != "RPAREN":
                raise ValueError("Missing closing parenthesis")
            self._advance()
            return value
        raise ValueError(f"Unexpected token {text!r}")


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
    try:
        result = _Parser(tokens).parse()
    except RecursionError:
        raise ValueError("Expression is nested too deeply")
    return float(result)
