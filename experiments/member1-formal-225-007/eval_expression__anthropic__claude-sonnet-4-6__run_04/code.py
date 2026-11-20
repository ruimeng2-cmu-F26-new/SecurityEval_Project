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
        r'(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)'  # number
        r'|(\*\*)'                                                  # **
        r'|([\+\-\*\/\(\)])'                                       # single-char operators/parens
        r')\s*'
    )
    tokens = []
    pos = 0
    s = expression
    while pos < len(s):
        m = token_pattern.match(s, pos)
        if not m or m.start() != pos:
            char = s[pos]
            if char.strip() == '':
                pos += 1
                continue
            raise ValueError(f"Unexpected character {char!r} at position {pos}")
        if m.group(1) is not None:
            tokens.append(('NUMBER', float(m.group(1))))
        elif m.group(2) is not None:
            tokens.append(('OP', '**'))
        elif m.group(3) is not None:
            ch = m.group(3)
            if ch in '+-*/':
                tokens.append(('OP', ch))
            elif ch == '(':
                tokens.append(('LPAREN', ch))
            elif ch == ')':
                tokens.append(('RPAREN', ch))
        pos = m.end()
    return tokens


class _Parser:
    """
    Grammar (with ** right-associative, standard precedence):
        expr   := term (('+' | '-') term)*
        term   := power (('*' | '/') power)*
        power  := unary ('**' unary)*   -- right-associative
        unary  := '-' unary | primary
        primary:= NUMBER | '(' expr ')'
    """

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    def _peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _consume(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _expect_number_or_expr(self):
        pass

    def parse(self) -> float:
        result = self._expr()
        if self.pos != len(self.tokens):
            raise ValueError(f"Unexpected token {self.tokens[self.pos]!r}")
        return result

    def _expr(self) -> float:
        left = self._term()
        while True:
            tok = self._peek()
            if tok and tok[0] == 'OP' and tok[1] in ('+', '-'):
                self._consume()
                right = self._term()
                if tok[1] == '+':
                    left += right
                else:
                    left -= right
            else:
                break
        return left

    def _term(self) -> float:
        left = self._power()
        while True:
            tok = self._peek()
            if tok and tok[0] == 'OP' and tok[1] in ('*', '/'):
                self._consume()
                right = self._power()
                if tok[1] == '*':
                    left *= right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    left /= right
            else:
                break
        return left

    def _power(self) -> float:
        base = self._unary()
        tok = self._peek()
        if tok and tok[0] == 'OP' and tok[1] == '**':
            self._consume()
            exp = self._power()  # right-associative
            return base ** exp
        return base

    def _unary(self) -> float:
        tok = self._peek()
        if tok and tok[0] == 'OP' and tok[1] == '-':
            self._consume()
            return -self._unary()
        if tok and tok[0] == 'OP' and tok[1] == '+':
            self._consume()
            return self._unary()
        return self._primary()

    def _primary(self) -> float:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if tok[0] == 'NUMBER':
            self._consume()
            return tok[1]
        if tok[0] == 'LPAREN':
            self._consume()
            value = self._expr()
            closing = self._peek()
            if closing is None or closing[0] != 'RPAREN':
                raise ValueError("Missing closing parenthesis")
            self._consume()
            return value
        raise ValueError(f"Unexpected token {tok!r}")
