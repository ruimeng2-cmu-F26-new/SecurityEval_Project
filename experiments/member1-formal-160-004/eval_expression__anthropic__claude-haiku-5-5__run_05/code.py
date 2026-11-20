import math
import re

_NUMBER_RE = re.compile(r'(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?')
_OPERATORS = ('**', '+', '-', '*', '/', '(', ')')
_MAX_DEPTH = 200


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
            tokens.append(('NUM', float(match.group(0))))
            pos = match.end()
            continue
        for op in _OPERATORS:
            if expression.startswith(op, pos):
                tokens.append(('OP', op))
                pos += len(op)
                break
        else:
            raise ValueError(
                f"unexpected character {char!r} at position {pos}"
            )
    return tokens


class _Parser:
    def __init__(self, tokens):
        self._tokens = tokens
        self._index = 0
        self._depth = 0

    def _peek(self):
        if self._index < len(self._tokens):
            return self._tokens[self._index]
        return None

    def _next(self):
        token = self._peek()
        if token is None:
            raise ValueError("unexpected end of expression")
        self._index += 1
        return token

    def _is_op(self, token, *ops):
        return token is not None and token[0] == 'OP' and token[1] in ops

    def _enter(self):
        self._depth += 1
        if self._depth > _MAX_DEPTH:
            raise ValueError("expression is nested too deeply")

    def _leave(self):
        self._depth -= 1

    def parse(self):
        if not self._tokens:
            raise ValueError("empty expression")
        value = self._expr()
        if self._peek() is not None:
            raise ValueError(f"unexpected token {self._peek()[1]!r}")
        return value

    def _expr(self):
        self._enter()
        value = self._term()
        while self._is_op(self._peek(), '+', '-'):
            op = self._next()[1]
            right = self._term()
            value = value + right if op == '+' else value - right
        self._leave()
        return value

    def _term(self):
        self._enter()
        value = self._unary()
        while self._is_op(self._peek(), '*', '/'):
            op = self._next()[1]
            right = self._unary()
            if op == '*':
                value = value * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                value = value / right
        self._leave()
        return value

    def _unary(self):
        self._enter()
        if self._is_op(self._peek(), '+', '-'):
            op = self._next()[1]
            operand = self._unary()
            result = -operand if op == '-' else operand
        else:
            result = self._power()
        self._leave()
        return result

    def _power(self):
        self._enter()
        base = self._primary()
        if self._is_op(self._peek(), '**'):
            self._next()
            exponent = self._unary()
            base = _safe_power(base, exponent)
        self._leave()
        return base

    def _primary(self):
        self._enter()
        token = self._next()
        if token[0] == 'NUM':
            result = token[1]
        elif self._is_op(token, '('):
            result = self._expr()
            closing = self._peek()
            if not self._is_op(closing, ')'):
                raise ValueError("missing closing parenthesis")
            self._next()
        else:
            raise ValueError(f"unexpected token {token[1]!r}")
        self._leave()
        return result


def _safe_power(base, exponent):
    try:
        result = base ** exponent
    except ZeroDivisionError:
        raise ValueError("division by zero")
    except OverflowError:
        raise ValueError("numeric overflow")
    if isinstance(result, complex):
        raise ValueError("result is not a real number")
    return result


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
    if not math.isfinite(result):
        raise ValueError("result is not a finite number")
    return result
