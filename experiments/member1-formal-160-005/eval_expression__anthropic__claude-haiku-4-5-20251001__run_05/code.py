import re
from typing import List, Tuple

def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not expression or not expression.strip():
        raise ValueError("Empty expression")
    
    # Tokenize the expression
    tokens = tokenize(expression)
    
    if not tokens:
        raise ValueError("Empty expression")
    
    # Parse and evaluate
    result, pos = parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError(f"Unexpected token at position {pos}")
    
    return result


def tokenize(expression: str) -> List[str]:
    """Tokenize an arithmetic expression into a list of tokens."""
    # Pattern to match numbers (integers and floats), operators, and parentheses
    pattern = r'(\d+\.?\d*|\.\d+|[+\-*/()\*])'
    tokens = re.findall(pattern, expression)
    
    # Validate that all non-whitespace characters are accounted for
    cleaned = re.sub(r'\s', '', expression)
    reconstructed = ''.join(tokens)
    
    if cleaned != reconstructed:
        raise ValueError("Invalid characters in expression")
    
    return tokens


def parse_expression(tokens: List[str], pos: int) -> Tuple[float, int]:
    """Parse and evaluate an expression (handles + and -)."""
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


def parse_term(tokens: List[str], pos: int) -> Tuple[float, int]:
    """Parse and evaluate a term (handles * and /)."""
    left, pos = parse_factor(tokens, pos)
    
    while pos < len(tokens) and tokens[pos] in ('*', '/'):
        op = tokens[pos]
        pos += 1
        right, pos = parse_factor(tokens, pos)
        if op == '*':
            left = left * right
        else:
            if right == 0:
                raise ValueError("Division by zero")
            left = left / right
    
    return left, pos


def parse_factor(tokens: List[str], pos: int) -> Tuple[float, int]:
    """Parse and evaluate a factor (handles ** and unary minus)."""
    # Handle unary minus or plus
    negate = False
    while pos < len(tokens) and tokens[pos] in ('+', '-'):
        if tokens[pos] == '-':
            negate = not negate
        pos += 1
    
    left, pos = parse_power(tokens, pos)
    
    if negate:
        left = -left
    
    return left, pos


def parse_power(tokens: List[str], pos: int) -> Tuple[float, int]:
    """Parse and evaluate a power expression (handles **)."""
    left, pos = parse_primary(tokens, pos)
    
    if pos < len(tokens) and tokens[pos] == '**':
        pos += 1
        # Right associative: a**b**c = a**(b**c)
        right, pos = parse_power(tokens, pos)
        left = left ** right
    
    return left, pos


def parse_primary(tokens: List[str], pos: int) -> Tuple[float, int]:
    """Parse a primary value (number or parenthesized expression)."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    token = tokens[pos]
    
    # Handle parenthesized expression
    if token == '(':
        pos += 1
        result, pos = parse_expression(tokens, pos)
        if pos >= len(tokens) or tokens[pos] != ')':
            raise ValueError("Missing closing parenthesis")
        pos += 1
        return result, pos
    
    # Handle number
    if re.match(r'^\d+\.?\d*$|^\.\d+$', token):
        try:
            value = float(token)
            return value, pos + 1
        except ValueError:
            raise ValueError(f"Invalid number: {token}")
    
    raise ValueError(f"Unexpected token: {token}")
