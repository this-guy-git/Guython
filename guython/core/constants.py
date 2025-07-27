import operator
import math

VERSION = "v2.1.0b25727"
MAX_LOOP_ITERATIONS = 10000

SAFE_OPERATIONS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '**': operator.pow,
    '^': operator.pow,  # Guython uses ^ for power
    '==': operator.eq,
    '!=': operator.ne,
    '<': operator.lt,
    '<=': operator.le,
    '>': operator.gt,
    '>=': operator.ge,
    'and': operator.and_,
    'or': operator.or_,
    'not': operator.not_,
}

SAFE_FUNCTIONS = {
    'abs': abs,
    'round': round,
    'int': int,
    'float': float,
    'str': str,
    'len': len,
    'max': max,
    'min': min,
    'sum': sum,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'pi': math.pi,
    'e': math.e,
}
