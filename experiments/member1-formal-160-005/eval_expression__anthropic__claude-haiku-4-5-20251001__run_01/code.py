def evaluate_expression(expression: str) -> float:
    """Evaluate an arithmetic expression such as "2 * (3 + 4) - 1.5" and return the
    result as a float. Numbers, parentheses, unary minus and the operators + - * / **
    are supported. Raise ValueError for malformed input such as "2 +" or an empty string.
    """
    if not expression or not expression.strip():
        raise ValueError("Empty expression")
    
    expression = expression.strip()
    tokens = _tokenize(expression)
    
    if not tokens:
        raise ValueError("Empty expression")
    
    result, pos = _parse_expression(tokens, 0)
    
    if pos != len(tokens):
        raise ValueError("Unexpected tokens after expression")
    
    return result


def _tokenize(expression: str) -> list:
    """Tokenize the expression into numbers, operators, and parentheses."""
    tokens = []
    i = 0
    
    while i < len(expression):
        char = expression[i]
        
        if char.isspace():
            i += 1
            continue
        
        if char.isdigit() or (char == '.' and i + 1 < len(expression) and expression[i + 1].isdigit()):
            j = i
            while j < len(expression) and (expression[j].isdigit() or expression[j] == '.'):
                j += 1
            tokens.append(('NUMBER', float(expression[i:j])))
            i = j
        elif char in '+-*/()**':
            if char == '*' and i + 1 < len(expression) and expression[i + 1] == '*':
                tokens.append(('OPERATOR', '**'))
                i += 2
            else:
                tokens.append(('OPERATOR', char))
                i += 1
        elif char == '(':
            tokens.append(('LPAREN', '('))
            i += 1
        elif char == ')':
            tokens.append(('RPAREN', ')'))
            i += 1
        else:
            raise ValueError(f"Invalid character: {char}")
    
    return tokens


def _parse_expression(tokens: list, pos: int) -> tuple:
    """Parse addition and subtraction (lowest precedence)."""
    left, pos = _parse_term(tokens, pos)
    
    while pos < len(tokens) and tokens[pos][0] == 'OPERATOR' and tokens[pos][1] in '+-':
        op = tokens[pos][1]
        pos += 1
        right, pos = _parse_term(tokens, pos)
        
        if op == '+':
            left = left + right
        else:
            left = left - right
    
    return left, pos


def _parse_term(tokens: list, pos: int) -> tuple:
    """Parse multiplication and division."""
    left, pos = _parse_power(tokens, pos)
    
    while pos < len(tokens) and tokens[pos][0] == 'OPERATOR' and tokens[pos][1] in '*/':
        op = tokens[pos][1]
        pos += 1
        right, pos = _parse_power(tokens, pos)
        
        if op == '*':
            left = left * right
        else:
            if right == 0:
                raise ValueError("Division by zero")
            left = left / right
    
    return left, pos


def _parse_power(tokens: list, pos: int) -> tuple:
    """Parse exponentiation (right associative)."""
    left, pos = _parse_unary(tokens, pos)
    
    if pos < len(tokens) and tokens[pos][0] == 'OPERATOR' and tokens[pos][1] == '**':
        pos += 1
        right, pos = _parse_power(tokens, pos)
        left = left ** right
    
    return left, pos


def _parse_unary(tokens: list, pos: int) -> tuple:
    """Parse unary minus and primary expressions."""
    if pos < len(tokens) and tokens[pos][0] == 'OPERATOR' and tokens[pos][1] in '+-':
        op = tokens[pos][1]
        pos += 1
        value, pos = _parse_unary(tokens, pos)
        
        if op == '-':
            value = -value
        
        return value, pos
    
    return _parse_primary(tokens, pos)


def _parse_primary(tokens: list, pos: int) -> tuple:
    """Parse numbers and parenthesized expressions."""
    if pos >= len(tokens):
        raise ValueError("Unexpected end of expression")
    
    token_type, token_value = tokens[pos]
    
    if token_type == 'NUMBER':
        return token_value, pos + 1
    
    if token_type == 'LPAREN':
        pos += 1
        result, pos = _parse_expression(tokens, pos)
        
        if pos >= len(tokens) or tokens[pos][0] != 'RPAREN':
            raise ValueError("Missing closing parenthesis")
        
        return result, pos + 1
    
    raise ValueError(f"Unexpected token: {token_value}")
