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
        r'(\*\*)'          # group 1: power operator
        r'|([+\-*/()])'    # group 2: single-char operators and parens
        r'|(\d+\.?\d*(?:[eE][+\-]?\d+)?|\.\d+(?:[eE][+\-]?\d+)?)'  # group 3: numbers
        r')\s*'
    )
    tokens = []
    pos = 0
    while pos < len(expression):
        m = token_pattern.match(expression, pos)
        if not m:
            remaining = expression[pos:].strip()
            if remaining:
                raise ValueError(f"Unexpected character at position {pos}: {expression[pos]!r}")
            break
        if m.group(1):
            tokens.append(('OP', '**'))
        elif m.group(2):
            tokens.append(('OP', m.group(2)))
        elif m.group(3):
            tokens.append(('NUM', m.group(3)))
        pos = m.end()
    return tokens


class _Parser:
    """Recursive descent parser for arithmetic expressions."""

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

    def expect(self, type_, value=None):
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] != type_:
            raise ValueError(f"Expected {type_!r} but got {token!r}")
        if value is not None and token[1] != value:
            raise ValueError(f"Expected {value!r} but got {token[1]!r}")
        return self.consume()

    def parse(self):
        result = self.parse_expr()
        if self.peek() is not None:
            raise ValueError(f"Unexpected token: {self.peek()!r}")
        return result

    # Grammar (lowest to highest precedence):
    # expr     -> term (('+' | '-') term)*
    # term     -> power (('*' | '/') power)*
    # power    -> unary ('**' unary)*   (right-associative)
    # unary    -> '-' unary | primary
    # primary  -> NUMBER | '(' expr ')'

    def parse_expr(self):
        left = self.parse_term()
        while True:
            token = self.peek()
            if token and token[0] == 'OP' and token[1] in ('+', '-'):
                op = self.consume()[1]
                right = self.parse_term()
                if op == '+':
                    left += right
                else:
                    left -= right
            else:
                break
        return left

    def parse_term(self):
        left = self.parse_power()
        while True:
            token = self.peek()
            if token and token[0] == 'OP' and token[1] in ('*', '/'):
                op = self.consume()[1]
                right = self.parse_power()
                if op == '*':
                    left *= right
                else:
                    if right == 0:
                        raise ValueError("Division by zero")
                    left /= right
            else:
                break
        return left

    def parse_power(self):
        base = self.parse_unary()
        token = self.peek()
        if token and token[0] == 'OP' and token[1] == '**':
            self.consume()
            # Right-associative: recurse into parse_power
            exp = self.parse_power()
            return base ** exp
        return base

    def parse_unary(self):
        token = self.peek()
        if token and token[0] == 'OP' and token[1] == '-':
            self.consume()
            return -self.parse_unary()
        if token and token[0] == 'OP' and token[1] == '+':
            self.consume()
            return self.parse_unary()
        return self.parse_primary()

    def parse_primary(self):
        token = self.peek()
        if token is None:
            raise ValueError("Unexpected end of expression")
        if token[0] == 'NUM':
            self.consume()
            return float(token[1])
        if token[0] == 'OP' and token[1] == '(':
            self.consume()
            value = self.parse_expr()
            self.expect('OP', ')')
            return value
        raise ValueError(f"Unexpected token: {token!r}")
