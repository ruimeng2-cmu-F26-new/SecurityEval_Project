import re

_NUMBER_RE = re.compile(r"(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
_OPERATORS = frozenset("+-*/()")


def _tokenize(text):
    tokens = []
    pos = 0
    length = len(text)
    while pos < length:
        ch = text[pos]
        if ch.isspace():
            pos += 1
            continue
        if text.startswith("**", pos):
            tokens.append(("OP", "**"))
            pos += 2
            continue
        if ch in _OPERATORS:
            tokens.append(("OP", ch))
            pos += 1
            continue
        match = _NUMBER_RE.match(text, pos)
        if match:
            try:
                value = float(match.group())
            except (OverflowError, ValueError):
                raise ValueError(f"invalid number {match.group()!r}")
            tokens.append(("NUM", value))
            pos = match.end()
            continue
        raise ValueError(f"unexpected character {ch!r} at position {pos}")
    return tokens


class _Parser:
    """Recursive descent parser that evaluates while parsing.

    Grammar:
        expression := term (('+' | '-') term)*
        term       := factor (('*' | '/') factor)*
        factor     := ('+' | '-') factor | power
        power      := atom ('**' factor)?
        atom       := NUMBER | '(' expression ')'
    """

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
            raise ValueError("unexpected end of expression")
        self._index += 1
        return token

    def _is_op(self, token, *symbols):
        return token is not None and token[0] == "OP" and token[1] in symbols

    def parse(self):
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expression()
        if self._peek() is not None:
            raise ValueError(f"unexpected token {self._peek()[1]!r}")
        return value

    def _expression(self):
        value = self._term()
        while self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            right = self._term()
            value = value + right if op == "+" else value - right
        return value

    def _term(self):
        value = self._factor()
        while self._is_op(self._peek(), "*", "/"):
            op = self._advance()[1]
            right = self._factor()
            if op == "*":
                value = value * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                value = value / right
        return value

    def _factor(self):
        if self._is_op(self._peek(), "+", "-"):
            op = self._advance()[1]
            operand = self._factor()
            return -operand if op == "-" else operand
        return self._power()

    def _power(self):
        base = self._atom()
        if self._is_op(self._peek(), "**"):
            self._advance()
            exponent = self._factor()
            try:
                result = base ** exponent
            except ZeroDivisionError:
                raise ValueError("division by zero in exponentiation")
            except OverflowError:
                raise ValueError("numeric overflow in exponentiation")
            if isinstance(result, complex):
                raise ValueError("exponentiation produced a complex result")
            return result
        return base

    def _atom(self):
        token = self._advance()
        if token[0] == "NUM":
            return token[1]
        if self._is_op(token, "("):
            value = self._expression()
            closing = self._peek()
            if not self._is_op(closing, ")"):
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
        raise ValueError("expression must be a string")
    tokens = _tokenize(expression)
    try:
        result = _Parser(tokens).parse()
    except RecursionError:
        raise ValueError("expression is nested too deeply")
    result = float(result)
    if result != result or result in (float("inf"), float("-inf")):
        raise ValueError("expression did not evaluate to a finite number")
    return result
