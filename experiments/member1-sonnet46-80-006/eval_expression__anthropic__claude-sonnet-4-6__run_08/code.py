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
        r'|(\*\*)'                         # ** (must come before *)
        r'|([+\-*/()])'                    # single-char operators and parens
        r')\s*'
    )
    tokens = []
    pos = 0
    while pos < len(expression):
        m = token_pattern.match(expression, pos)
        if not m:
            ch = expression[pos]
            if ch.strip():
                raise ValueError(f"Unexpected character: {ch!r}")
            pos += 1
            continue
        if m.start() != pos:
            skipped = expression[pos:m.start()]
            if skipped.strip():
                raise ValueError(f"Unexpected characters: {skipped!r}")
        if m.group(1) is not None:
            tokens.append(('NUMBER', float(m.group(1))))
        elif m.group(2) is not None:
            tokens.append(('OP', '**'))
        elif m.group(3) is not None:
            ch = m.group(3)
            if ch == '(':
                tokens.append(('LPAREN', ch))
            elif ch == ')':
                tokens.append(('RPAREN', ch))
            else:
                tokens.append(('OP', ch))
        pos = m.end()
    return tokens


class _Parser:
    """Recursive descent parser for arithmetic expressions.

    Grammar (with precedence, low to high):
        expr   : term (('+' | '-') term)*
        term   : factor (('*' | '/') factor)*
        factor : power
        power  : unary ('**' unary)*   (right-associative)
        unary  : '-' unary | primary
        primary: NUMBER | '(' expr ')'
    """

    def __init__(self, tokens: list):
        self._tokens = tokens
        self._pos = 0

    def _peek(self):
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self):
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _expect(self, kind, value=None):
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if tok[0] != kind:
            raise ValueError(f"Expected {kind} but got {tok}")
        if value is not None and tok[1] != value:
            raise ValueError(f"Expected {value!r} but got {tok[1]!r}")
        return self._consume()

    def parse(self):
        result = self._expr()
        if self._pos != len(self._tokens):
            raise ValueError(f"Unexpected token: {self._peek()}")
        return result

    def _expr(self):
        left = self._term()
        while True:
            tok = self._peek()
            if tok and tok[0] == 'OP' and tok[1] in ('+', '-'):
                self._consume()
                right = self._term()
                if tok[1] == '+':
                    left = left + right
                else:
                    left = left - right
            else:
                break
        return left

    def _term(self):
        left = self._power()
        while True:
            tok = self._peek()
            if tok and tok[0] == 'OP' and tok[1] in ('*', '/'):
                self._consume()
                right = self._power()
                if tok[1] == '*':
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
        tok = self._peek()
        if tok and tok[0] == 'OP' and tok[1] == '**':
            self._consume()
            exp = self._power()  # right-associative
            return base ** exp
        return base

    def _unary(self):
        tok = self._peek()
        if tok and tok[0] == 'OP' and tok[1] == '-':
            self._consume()
            return -self._unary()
        if tok and tok[0] == 'OP' and tok[1] == '+':
            self._consume()
            return self._unary()
        return self._primary()

    def _primary(self):
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if tok[0] == 'NUMBER':
            self._consume()
            return tok[1]
        if tok[0] == 'LPAREN':
            self._consume()
            val = self._expr()
            self._expect('RPAREN')
            return val
        raise ValueError(f"Unexpected token: {tok}")
