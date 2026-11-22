import re

def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    expression = expression.strip()
    
    if not expression:
        raise ValueError("Empty expression")
    
    tokens = tokenize(expression)
    
    if not tokens:
        raise ValueError("Empty expression")
    
    result, pos = parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError(f"Unexpected token at position {pos}: {tokens[pos]}")
    
    return result


def tokenize(expression: str) -> list:
    """Tokenize the expression into numbers, operators, and parentheses."""
    token_pattern = r'(\d+\.?\d*|\.\d+|[+\-*/()**])'
    tokens = re.findall(token_pattern, expression)
    
    # Validate that the expression only contains valid characters
    cleaned = re.sub(r'\s+', '', expression)
    if ''.join(tokens) != cleaned:
        raise ValueError(f"Invalid characters in expression")
    
    return tokens


def parse_expression(tokens: list, pos: int) -> tuple:
    """Parse addition and subtraction (lowest precedence)."""
    left, pos = parse_term(tokens, pos)
    
    while pos < len(tokens) and tokens[pos] in ('+', '-'):
        op = tokens[pos]
        pos += 1
        right, pos = parse_term(tokens, pos)
        if op == '+':
            left = left + right
        else:
            left = left - right
    
    return left, pos


def parse_term(tokens: list, pos: int) -> tuple:
    """Parse multiplication and division."""
    left, pos = parse_power(tokens, pos)
    
    while pos < len(tokens) and tokens[pos] in ('*', '/'):
        op = tokens[pos]
        pos += 1
        right, pos = parse_power(tokens, pos)
        if op == '*':
            left = left * right
        else:
            if right == 0:
                raise ValueError("Division by zero")
            left = left / right
    
    return left, pos


def parse_power(tokens: list, pos: int) -> tuple:
    """Parse exponentiation (right-associative)."""
    left, pos = parse_unary(tokens, pos)
    
    if pos < len(tokens) and tokens[pos] == '**':
        pos += 1
        right, pos = parse_power(tokens, pos)  # Right-associative
        left = left ** right
    
    return left, pos


def parse_unary(tokens: list, pos: int) -> tuple:
    """Parse unary operators (+ and -)."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    if tokens[pos] == '-':
        pos += 1
        value, pos = parse_unary(tokens, pos)
        return -value, pos
    elif tokens[pos] == '+':
        pos += 1
        return parse_unary(tokens, pos)
    
    return parse_primary(tokens, pos)


def parse_primary(tokens: list, pos: int) -> tuple:
    """Parse primary values: numbers and parenthesized expressions."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    token = tokens[pos]
    
    if token == '(':
        pos += 1
        value, pos = parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise ValueError("Missing closing parenthesis")
        pos += 1
        return value, pos
    
    try:
        value = float(token)
        return value, pos + 1
    except ValueError:
        raise ValueError(f"Expected number or '(', got '{token}'")
