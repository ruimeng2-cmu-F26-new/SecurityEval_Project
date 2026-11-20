import re

_TOKEN_PATTERN = re.compile(
    r"\s*(?:"
    r"(?P<number>(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)"
    r"|(?P<op>\*\*|[+\-*/])"
    r"|(?P<lparen>\()"
    r"|(?P<rparen>\))"
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
        match = _TOKEN_PATTERN.match(expression, pos)
        if not match or match.end() == pos:
            raise ValueError(
                f"Unexpected character {expression[pos]!r} at position {pos}"
            )
        if match.group("number") is not None:
            tokens.append(("number", match.group("number")))
        elif match.group("op") is not None:
            tokens.append(("op", match.group("op")))
        elif match.group("lparen") is not None:
            tokens.append(("lparen", "("))
        elif match.group("rparen") is not None:
            tokens.append(("rparen", ")"))
        pos = match.end()
    return tokens


class _Parser:
    """Recursive-descent parser implementing the grammar:

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
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        self._pos += 1
        return token

    def _is_op(self, token, *values) -> bool:
        return token is not None and token[0] == "op" and token[1] in values

    def parse(self) -> float:
        if not self._tokens:
            raise ValueError("Empty expression")
        value = self._parse_expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token {self._peek()[1]!r}")
        return value

    def _parse_expr(self) -> float:
        value = self._parse_term()
        while self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            right = self._parse_term()
            value = value + right if op == "+" else value - right
        return value

    def _parse_term(self) -> float:
        value = self._parse_unary()
        while self._is_op(self._peek(), "*", "/"):
            op = self._advance()[1]
            right = self._parse_unary()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                value = value / right
        return value

    def _parse_unary(self) -> float:
        if self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            operand = self._parse_unary()
            return -operand if op == "-" else operand
        return self._parse_power()

    def _parse_power(self) -> float:
        base = self._parse_primary()
        if self._is_op(self._peek(), "**"):
            self._advance()
            exponent = self._parse_unary()
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

    def _parse_primary(self) -> float:
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        kind, text = token
        if kind == "number":
            self._advance()
            try:
                return float(text)
            except ValueError:
                raise ValueError(f"Invalid number {text!r}")
        if kind == "lparen":
            self._advance()
            value = self._parse_expr()
            closing = self._peek()
            if closing is None or closing[0] != "rparen":
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
        raise TypeError("expression must be a string")
    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    try:
        result = _Parser(tokens).parse()
    except RecursionError:
        raise ValueError("Expression is nested too deeply")
    return float(result)
