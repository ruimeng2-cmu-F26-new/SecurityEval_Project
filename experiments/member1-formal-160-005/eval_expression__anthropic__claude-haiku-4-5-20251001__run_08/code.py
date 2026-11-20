import re
from typing import Union


def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not expression or not expression.strip():
        raise ValueError("Empty expression")
    
    expression = expression.strip()
    
    tokens = tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    
    result, pos = parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError(f"Unexpected token at position {pos}")
    
    return result


def tokenize(expression: str) -> list:
    """Tokenize the expression into numbers, operators, and parentheses."""
    token_pattern = r'(\d+\.?\d*|\.\d+|[+\-*/()**])'
    tokens = re.findall(token_pattern, expression)
    
    if not tokens:
        raise ValueError("Invalid expression")
    
    cleaned = []
    for token in tokens:
        if re.match(r'^\d+\.?\d*$', token) or re.match(r'^\.\d+$', token):
            cleaned.append(('NUMBER', float(token)))
        elif token in '+-*/**()':
            cleaned.append(('OP', token))
        else:
            raise ValueError(f"Invalid token: {token}")
    
    return cleaned


def parse_expression(tokens: list, pos: int) -> tuple:
    """Parse addition and subtraction (lowest precedence)."""
    left, pos = parse_term(tokens, pos)
    
    while pos < len(tokens) and tokens[pos][0] == 'OP' and tokens[pos][1] in '+-':
        op = tokens[pos][1]
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
    
    while pos < len(tokens) and tokens[pos][0] == 'OP' and tokens[pos][1] in '*/':
        op = tokens[pos][1]
        pos += 1
        right, pos = parse_power(tokens, pos)
        
        if op == '*':
            left = left * right
        elif op == '/':
            if right == 0:
                raise ValueError("Division by zero")
            left = left / right
    
    return left, pos


def parse_power(tokens: list, pos: int) -> tuple:
    """Parse exponentiation (right-associative)."""
    left, pos = parse_unary(tokens, pos)
    
    if pos < len(tokens) and tokens[pos][0] == 'OP' and tokens[pos][1] == '**':
        pos += 1
        right, pos = parse_power(tokens, pos)
        left = left ** right
    
    return left, pos


def parse_unary(tokens: list, pos: int) -> tuple:
    """Parse unary minus and plus."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    if tokens[pos][0] == 'OP' and tokens[pos][1] in '+-':
        op = tokens[pos][1]
        pos += 1
        value, pos = parse_unary(tokens, pos)
        
        if op == '-':
            value = -value
        
        return value, pos
    
    return parse_primary(tokens, pos)


def parse_primary(tokens: list, pos: int) -> tuple:
    """Parse primary expressions (numbers and parenthesized expressions)."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    token_type, token_value = tokens[pos]
    
    if token_type == 'NUMBER':
        return token_value, pos + 1
    
    if token_type == 'OP' and token_value == '(':
        pos += 1
        result, pos = parse_expression(tokens, pos)
        
        if pos >= len(tokens) or tokens[pos][0] != 'OP' or tokens[pos][1] != ')':
            raise ValueError("Missing closing parenthesis")
        
        return result, pos + 1
    
    raise ValueError(f"Unexpected token: {token_value}")
