import re
from sympy import Eq, simplify, sympify
from typing import Tuple
from core.symbol_maps import phrase_to_symbol

# ----------------------------------------
# Convert Phrases to Symbolic Form
# Example: "mass times acceleration" → "m * a"
# ----------------------------------------
def convert_to_symbolic(text: str) -> str:
    """
    Replaces common natural language phrases with symbolic math equivalents.
    """
    for phrase, symbol in phrase_to_symbol.items():
        pattern = rf'\b{re.escape(phrase)}\b'
        text = re.sub(pattern, symbol, text, flags=re.IGNORECASE)
    return text

# ----------------------------------------
# Normalize Math Input
# Ensures compatibility with SymPy by cleaning common formatting issues.
# ----------------------------------------
def normalize_math_input(text: str) -> str:
    """
    Normalizes math expressions to prepare for symbolic parsing:
    - Replaces ^ with ** (exponentiation)
    - Replaces × with *
    - Replaces minus symbols, trims whitespace
    - Standardizes pi and other symbols
    """
    return (
        text.replace('^', '**')
            .replace('×', '*')
            .replace('−', '-')  # Unicode minus to ASCII minus
            .replace('π', 'pi')
            .strip()
    )

# ----------------------------------------
# Detect Whether Text is Likely a Math Expression
# ----------------------------------------
def is_math_expression(text: str) -> bool:
    """
    Heuristic to detect if a string looks like a math equation.
    """
    # First, check if this is clearly a description rather than an expression
    # These patterns indicate it's a description, not a math expression
    description_patterns = [
        r'\b(formula for|equation for|formula of|equation of)\b',
        r'\b(change in|difference in|sum of|product of)\b',
        r'\b(rate law|theorem|law|principle)\b',
        r'\b(integral of|derivative of|limit of)\b',
        r'\b(could not parse|formula for)\b'
    ]
    
    for pattern in description_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False
    
    # Check for mathematical symbols (but be more specific)
    # Look for actual mathematical expressions, not just descriptions
    math_symbols = re.search(r'[=^*/π+\-]', text)
    
    # Check for mathematical keywords that indicate equations
    equation_keywords = re.search(r'\b(equals|times|divided|squared|cubed)\b', text, re.IGNORECASE)
    
    # Check for formula/equation indicators (but not when they're part of explanations)
    # More restrictive: only if it's a standalone formula mention
    formula_indicators = (
        re.search(r'\b(formula|equation)\b', text, re.IGNORECASE) and 
        not re.search(r'\b(explains|describes|what|how|why|for|of)\b', text, re.IGNORECASE) and
        # Must also contain actual mathematical content
        re.search(r'[=+\-*/^]', text)
    )
    
    # Check for number patterns with operators
    number_patterns = re.search(r'\d+\s*[\+\-\*\/\^]\s*\d+', text)
    
    # Check for variable patterns (single letters that might be variables)
    # More restrictive: must be actual mathematical expressions
    variable_patterns = re.search(r'\b[a-zA-Z]\s*[=+\-*/]\s*[a-zA-Z0-9]', text)
    
    # Check for specific math phrases that indicate equations
    math_phrases = re.search(r'\b(equals|times|divided by|plus|minus|multiplied by)\b', text, re.IGNORECASE)
    
    # Additional check: must contain actual mathematical operators or equals sign
    has_math_operators = re.search(r'[=+\-*/^]', text)
    
    # Only return True if we have both mathematical content AND it's not clearly a description
    return bool(
        has_math_operators and 
        (math_symbols or equation_keywords or formula_indicators or number_patterns or variable_patterns or math_phrases)
    )

# ----------------------------------------
# Prepare expression for SymPy parsing
# ----------------------------------------
def prepare_for_sympy(expr: str) -> str:
    """
    Prepare a mathematical expression for SymPy parsing.
    """
    # Remove extra spaces but keep essential ones
    expr = re.sub(r'\s+', ' ', expr.strip())
    
    # Ensure proper spacing around operators
    expr = re.sub(r'([a-zA-Z0-9])\*([a-zA-Z0-9])', r'\1 * \2', expr)
    expr = re.sub(r'([a-zA-Z0-9])/([a-zA-Z0-9])', r'\1 / \2', expr)
    expr = re.sub(r'([a-zA-Z0-9])\+([a-zA-Z0-9])', r'\1 + \2', expr)
    expr = re.sub(r'([a-zA-Z0-9])-([a-zA-Z0-9])', r'\1 - \2', expr)
    
    # Handle exponents
    expr = re.sub(r'([a-zA-Z0-9])\*\*([a-zA-Z0-9])', r'\1**\2', expr)
    
    # Handle parentheses
    expr = re.sub(r'([a-zA-Z0-9])\(', r'\1 * (', expr)
    expr = re.sub(r'\)([a-zA-Z0-9])', r') * \1', expr)
    
    return expr

# ----------------------------------------
# Compare Two Expressions Using SymPy
# Supports math entered in natural language or symbolic form
# ----------------------------------------
def compare_math_expressions(rule_text: str, student_answer: str) -> Tuple[bool, float]:
    """
    Compares two math expressions after converting and normalizing.

    Returns:
        (matched: bool, score: float)
        - matched: True if expressions are symbolically equal
        - score: 1.0 if matched, else 0.0
    """
    try:
        # First, check if either input is clearly a description rather than a math expression
        description_patterns = [
            r'\b(formula for|equation for|formula of|equation of)\b',
            r'\b(change in|difference in|sum of|product of)\b',
            r'\b(rate law|theorem|law|principle)\b',
            r'\b(integral of|derivative of|limit of)\b',
            r'\b(could not parse|formula for)\b'
        ]
        
        for pattern in description_patterns:
            if re.search(pattern, rule_text, re.IGNORECASE) or re.search(pattern, student_answer, re.IGNORECASE):
                # This is a description, not a math expression - fall back to semantic matching
                return False, 0.0
        
        # Convert phrases like "mass times acceleration" to symbols
        rule_expr = convert_to_symbolic(rule_text)
        student_expr = convert_to_symbolic(student_answer)

        # Normalize symbols (e.g., ^ → **)
        rule_clean = normalize_math_input(rule_expr)
        student_clean = normalize_math_input(student_expr)

        # Prepare for SymPy parsing
        rule_clean = prepare_for_sympy(rule_clean)
        student_clean = prepare_for_sympy(student_clean)

        # Use sympy to parse and simplify
        rule_sym = simplify(sympify(rule_clean))
        student_sym = simplify(sympify(student_clean))

        # Compare expressions mathematically
        is_equal = Eq(rule_sym, student_sym)
        return bool(is_equal), 1.0

    except Exception as e:
        # Simple error logging without recursive calls
        print(f"[Math Match Error] Failed to parse math expressions")
        
        # Fallback to simple string comparison for basic cases
        try:
            # Use the cleaned versions that were prepared for SymPy
            rule_simple = re.sub(r'\s+', '', rule_clean.lower())
            student_simple = re.sub(r'\s+', '', student_clean.lower())
            if rule_simple == student_simple:
                return True, 1.0
        except:
            pass
        return False, 0.0 