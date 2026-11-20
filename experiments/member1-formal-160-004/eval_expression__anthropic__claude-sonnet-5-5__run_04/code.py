import re

_TOKEN_RE = re.compile(r"\s*(?:(\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)|(\*\*|[-+*/()]))")


def _tokenize(expression):
    tokens = []
    pos = 0
    n = len(expression)
    while pos < n:
        if expression[pos:].strip() == "":
            break
        m = _TOKEN_RE.match(expression, pos)
        if not m:
            raise ValueError("Invalid character at position %d" % pos)
        if m.group(1) is not None:
            try:
                tokens.append(("num", float(m.group(1))))
            except ValueError:
                raise ValueError("Invalid number")
        else:
            tokens.append(("op", m.group(2)))
        pos = m.end()
    return tokens


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return None

    def next(self):
        t = self.peek()
        if t is not None:
            self.i += 1
        return t

    def is_op(self, *ops):
        t = self.peek()
        return t is not None and t[0] == "op" and t[1] in ops

    def parse(self):
        if not self.tokens:
            raise ValueError("Empty expression")
        v = self.expr()
        if self.peek() is not None:
            raise ValueError("Unexpected token")
        return v

    def expr(self):
        v = self.term()
        while self.is_op("+", "-"):
            op = self.next()[1]
            r = self.term()
            v = v + r if op == "+" else v - r
        return v

    def term(self):
        v = self.unary()
        while self.is_op("*", "/"):
            op = self.next()[1]
            r = self.unary()
            if op == "*":
                v = v * r
            else:
                if r == 0:
                    raise ValueError("Division by zero")
                v = v / r
        return v

    def unary(self):
        if self.is_op("+", "-"):
            op = self.next()[1]
            v = self.unary()
            return -v if op == "-" else v
        return self.power()

    def power(self):
        base = self.atom()
        if self.is_op("**"):
            self.next()
            exp = self.unary()  # right associative, allows unary minus in exponent
            try:
                result = base ** exp
            except ZeroDivisionError:
                raise ValueError("Division by zero")
            except OverflowError:
                raise ValueError("Result too large")
            if isinstance(result, complex):
                raise ValueError("Complex result")
            return float(result)
        return base

    def atom(self):
        t = self.next()
        if t is None:
            raise ValueError("Unexpected end of expression")
        if t[0] == "num":
            return t[1]
        if t[1] == "(":
            v = self.expr()
            if not self.is_op(")"):
                raise ValueError("Missing closing parenthesis")
            self.next()
            return v
        raise ValueError("Unexpected token %r" % (t[1],))


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not isinstance(expression, str):
        raise ValueError("Expression must be a string")
    tokens = _tokenize(expression)
    return float(_Parser(tokens).parse())
