import re

_NUMBER_PATTERN = re.compile(r'(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?')
_OPERATOR_PATTERN = re.compile(r'\*\*|[+\-*/()]')


def _tokenize(expression):
    tokens = []
    pos = 0
    length = len(expression)
    while pos < length:
        ch = expression[pos]
        if ch.isspace():
            pos += 1
            continue
        match = _NUMBER_PATTERN.match(expression, pos)
        if match:
            tokens.append(('NUM', match.group(0)))
            pos = match.end()
            continue
        match = _OPERATOR_PATTERN.match(expression, pos)
        if match:
            tokens.append(('OP', match.group(0)))
            pos = match.end()
            continue
        raise ValueError(f"Unexpected character {ch!r} at position {pos}")
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

    def _match_op(self, *ops):
        token = self._peek()
        if token is not None and token[0] == 'OP' and token[1] in ops:
            self._pos += 1
            return token[1]
        return None

    def parse(self):
        if not self._tokens:
            raise ValueError("Empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token {self._peek()[1]!r}")
        return value

    def _expr(self):
        value = self._term()
        while True:
            op = self._match_op('+', '-')
            if op is None:
                break
            right = self._term()
            value = value + right if op == '+' else value - right
        return value

    def _term(self):
        value = self._unary()
        while True:
            op = self._match_op('*', '/')
            if op is None:
                break
            right = self._unary()
            if op == '*':
                value = value * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                value = value / right
        return value

    def _unary(self):
        op = self._match_op('+', '-')
        if op is not None:
            operand = self._unary()
            return -operand if op == '-' else operand
        return self._power()

    def _power(self):
        base = self._atom()
        if self._match_op('**') is not None:
            exponent = self._unary()
            return base ** exponent
        return base

    def _atom(self):
        token = self._advance()
        kind, text = token
        if kind == 'NUM':
            return float(text)
        if text == '(':
            value = self._expr()
            closing = self._peek()
            if closing is None or closing != ('OP', ')'):
                raise ValueError("Missing closing parenthesis")
            self._pos += 1
            return value
        raise ValueError(f"Unexpected token {text!r}")


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
    except OverflowError as exc:
        raise ValueError("Numeric overflow while evaluating expression") from exc

    if isinstance(result, complex):
        raise ValueError("Expression produces a complex result")
    return float(result)
