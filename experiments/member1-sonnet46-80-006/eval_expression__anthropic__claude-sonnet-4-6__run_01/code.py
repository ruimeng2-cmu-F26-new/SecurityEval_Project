import re


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not expression or not expression.strip():
        raise ValueError("Empty expression")

    tokens = _tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")

    parser = _Parser(tokens)
    result = parser.parse()
    return float(result)


def _tokenize(expression: str) -> list:
    token_pattern = re.compile(
        r'\s*(?:'
        r'(\d+\.?\d*(?:[eE][+-]?\d+)?)'  # number
        r'|(\*\*)'                          # ** (must come before *)
        r'|([+\-*/()])'                     # single char operators and parens
        r')\s*'
    )
    tokens = []
    pos = 0
    while pos < len(expression):
        match = token_pattern.match(expression, pos)
        if not match:
            char = expression[pos]
            if not char.strip():
                pos += 1
                continue
            raise ValueError(f"Unexpected character: {char!r}")
        if match.group(1) is not None:
            tokens.append(('NUMBER', float(match.group(1))))
        elif match.group(2) is not None:
            tokens.append(('OP', '**'))
        elif match.group(3) is not None:
            tokens.append(('OP', match.group(3)))
        pos = match.end()
    return tokens


class _Parser:
    """Recursive descent parser for arithmetic expressions.

    Grammar (highest precedence last in recursion → first in grammar):
        expr    : term (('+' | '-') term)*
        term    : factor (('*' | '/') factor)*
        factor  : power
        power   : unary ('**' unary)*  -- right-associative
        unary   : '-' unary | primary
        primary : NUMBER | '(' expr ')'
    """

    def __init__(self, tokens: list):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self):
        token = self._tokens[self._pos]
        self._pos += 1
        return token

    def _expect(self, kind, value=None):
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] != kind or (value is not None and token[1] != value):
            raise ValueError(f"Expected {kind} {value!r}, got {token!r}")
        return self._consume()

    def parse(self):
        result = self._expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token: {self._peek()!r}")
        return result

    def _expr(self):
        left = self._term()
        while True:
            token = self._peek()
            if token and token[0] == 'OP' and token[1] in ('+', '-'):
                op = self._consume()[1]
                right = self._term()
                if op == '+':
                    left += right
                else:
                    left -= right
            else:
                break
        return left

    def _term(self):
        left = self._power()
        while True:
            token = self._peek()
            if token and token[0] == 'OP' and token[1] in ('*', '/'):
                op = self._consume()[1]
                right = self._power()
                if op == '*':
                    left *= right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    left /= right
            else:
                break
        return left

    def _power(self):
        base = self._unary()
        token = self._peek()
        if token and token[0] == 'OP' and token[1] == '**':
            self._consume()
            exp = self._power()  # right-associative
            return base ** exp
        return base

    def _unary(self):
        token = self._peek()
        if token and token[0] == 'OP' and token[1] == '-':
            self._consume()
            return -self._unary()
        if token and token[0] == 'OP' and token[1] == '+':
            self._consume()
            return self._unary()
        return self._primary()

    def _primary(self):
        token = self._peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] == 'NUMBER':
            self._consume()
            return token[1]
        if token[0] == 'OP' and token[1] == '(':
            self._consume()
            value = self._expr()
            self._expect('OP', ')')
            return value
        raise ValueError(f"Unexpected token: {token!r}")
