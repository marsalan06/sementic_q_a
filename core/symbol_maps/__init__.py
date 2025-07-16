from .physics import physics_phrase_to_symbol
from .math import math_phrase_to_symbol
from .chemistry import chemistry_phrase_to_symbol
from .greek import greek_phrase_to_symbol
from .operators import operators_phrase_to_symbol

# Merge all mappings into a single dictionary
phrase_to_symbol = {}
for d in [physics_phrase_to_symbol, math_phrase_to_symbol, chemistry_phrase_to_symbol, greek_phrase_to_symbol, operators_phrase_to_symbol]:
    phrase_to_symbol.update(d) 