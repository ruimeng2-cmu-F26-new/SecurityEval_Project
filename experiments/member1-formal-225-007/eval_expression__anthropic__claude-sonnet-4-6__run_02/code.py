import re
from typing import List


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


def _tokenize(expression: str) -> List[str]:
    token_pattern = re.compile(
        r'\s*(\d+\.?\d*|\.\d+|[+\-*/()^]|\*\*)\s*'
    )
    tokens = []
    pos = 0
    while pos < len(expression):
        m = token_pattern.match(expression, pos)
        if m:
            tok = m.group(1)
            tokens.append(tok)
            pos = m.end()
        elif expression[pos].isspace():
            pos += 1
        else:
            raise ValueError(f"Unexpected character: {expression[pos]!r}")
    return tokens


class _Parser:
    """Recursive descent parser for arithmetic expressions.

    Grammar:
        expr   : term (('+' | '-') term)*
        term   : factor (('*' | '/') factor)*
        factor : unary '**' factor  (right-associative)
               | unary
        unary  : '-' unary
               | primary
        primary: NUMBER | '(' expr ')'
    """

    def __init__(self, tokens: List[str]):
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

    def _expect(self, value: str):
        tok = self._peek()
        if tok != value:
            raise ValueError(f"Expected {value!r} but got {tok!r}")
        return self._consume()

    def parse(self) -> float:
        result = self._expr()
        if self._pos != len(self._tokens):
            raise ValueError(f"Unexpected token: {self._peek()!r}")
        return result

    def _expr(self) -> float:
        left = self._term()
        while self._peek() in ('+', '-'):
            op = self._consume()
            right = self._term()
            if op == '+':
                left += right
            else:
                left -= right
        return left

    def _term(self) -> float:
        left = self._factor()
        while self._peek() in ('*', '/'):
            # Make sure we don't consume '**' as '*'
            # Tokenizer should handle '**' as a single token
            op = self._consume()
            right = self._factor()
            if op == '*':
                left *= right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                left /= right
        return left

    def _factor(self) -> float:
        # Right-associative exponentiation
        base = self._unary()
        if self._peek() == '**':
            self._consume()
            exp = self._factor()  # right-associative
            return base ** exp
        return base

    def _unary(self) -> float:
        if self._peek() == '-':
            self._consume()
            return -self._unary()
        if self._peek() == '+':
            self._consume()
            return self._unary()
        return self._primary()

    def _primary(self) -> float:
        tok = self._peek()
        if tok is None:
            raise ValueError("Unexpected end of expression")
        if tok == '(':
            self._consume()
            val = self._expr()
            self._expect(')')
            return val
        # Try to parse as a number
        try:
            val = float(tok)
            self._consume()
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Unexpected token: {tok!r}")
