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
        r'(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)'  # numbers
        r'|(\*\*)'                                                 # **
        r'|([+\-*/()])'                                           # single-char operators and parens
        r')\s*'
    )
    tokens = []
    pos = 0
    s = expression
    while pos < len(s):
        m = token_pattern.match(s, pos)
        if not m:
            remaining = s[pos:].strip()
            if remaining:
                raise ValueError(f"Unexpected character at position {pos}: {s[pos]!r}")
            break
        if m.group(1) is not None:
            tokens.append(('NUMBER', float(m.group(1))))
        elif m.group(2) is not None:
            tokens.append(('OP', '**'))
        elif m.group(3) is not None:
            tokens.append(('OP', m.group(3)))
        pos = m.end()
    return tokens


class _Parser:
    """Recursive descent parser for arithmetic expressions.

    Grammar:
        expr    ::= term (('+' | '-') term)*
        term    ::= factor (('*' | '/') factor)*
        factor  ::= ('+' | '-') factor | power
        power   ::= primary ('**' factor)*   (right-associative)
        primary ::= NUMBER | '(' expr ')'
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, kind, value=None):
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] != kind or (value is not None and token[1] != value):
            raise ValueError(f"Expected {kind} {value!r}, got {token!r}")
        return self.consume()

    def parse(self):
        result = self.expr()
        if self.pos < len(self.tokens):
            raise ValueError(f"Unexpected token: {self.tokens[self.pos]!r}")
        return result

    def expr(self):
        left = self.term()
        while True:
            token = self.peek()
            if token and token[0] == 'OP' and token[1] in ('+', '-'):
                self.consume()
                right = self.term()
                if token[1] == '+':
                    left += right
                else:
                    left -= right
            else:
                break
        return left

    def term(self):
        left = self.factor()
        while True:
            token = self.peek()
            if token and token[0] == 'OP' and token[1] in ('*', '/'):
                self.consume()
                right = self.factor()
                if token[1] == '*':
                    left *= right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    left /= right
            else:
                break
        return left

    def factor(self):
        token = self.peek()
        if token and token[0] == 'OP' and token[1] in ('+', '-'):
            self.consume()
            operand = self.factor()
            return operand if token[1] == '+' else -operand
        return self.power()

    def power(self):
        base = self.primary()
        token = self.peek()
        if token and token[0] == 'OP' and token[1] == '**':
            self.consume()
            exp = self.factor()  # right-associative
            return base ** exp
        return base

    def primary(self):
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] == 'NUMBER':
            self.consume()
            return token[1]
        if token[0] == 'OP' and token[1] == '(':
            self.consume()
            value = self.expr()
            self.expect('OP', ')')
            return value
        raise ValueError(f"Unexpected token: {token!r}")
