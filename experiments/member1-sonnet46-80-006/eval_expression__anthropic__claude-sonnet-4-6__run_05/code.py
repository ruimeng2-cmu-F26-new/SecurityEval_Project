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


def _tokenize(expression: str):
    token_pattern = re.compile(
        r'\s*(?:'
        r'(\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?'  # numbers
        r'|(\*\*|[+\-*/()])'                     # operators and parens
        r')\s*'
    )
    tokens = []
    pos = 0
    while pos < len(expression):
        m = token_pattern.match(expression, pos)
        if not m or m.start() != pos:
            stripped = expression[pos:].strip()
            if stripped:
                raise ValueError(f"Unexpected character at position {pos}: {expression[pos]!r}")
            break
        if m.group(1) is not None:
            tokens.append(('NUMBER', float(m.group(0).strip())))
        elif m.group(2) is not None:
            tokens.append(('OP', m.group(2).strip()))
        pos = m.end()
    return tokens


class _Parser:
    """Recursive descent parser for arithmetic expressions.

    Grammar (highest to lowest precedence):
        expr    : term (('+' | '-') term)*
        term    : power (('*' | '/') power)*
        power   : unary ('**' unary)*   # right-associative
        unary   : ('-' | '+') unary | primary
        primary : NUMBER | '(' expr ')'
    """

    def __init__(self, tokens):
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
            raise ValueError(f"Expected {value!r}, got {token[1]!r}")
        return self._consume()

    def parse(self):
        result = self._expr()
        if self._peek() is not None:
            raise ValueError(f"Unexpected token: {self._peek()[1]!r}")
        return result

    def _expr(self):
        left = self._term()
        while True:
            token = self._peek()
            if token and token[0] == 'OP' and token[1] in ('+', '-'):
                self._consume()
                right = self._term()
                if token[1] == '+':
                    left = left + right
                else:
                    left = left - right
            else:
                break
        return left

    def _term(self):
        left = self._power()
        while True:
            token = self._peek()
            if token and token[0] == 'OP' and token[1] in ('*', '/'):
                self._consume()
                right = self._power()
                if token[1] == '*':
                    left = left * right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    left = left / right
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
            return +self._unary()
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
        raise ValueError(f"Unexpected token: {token[1]!r}")
