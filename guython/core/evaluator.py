import re
import ast
from typing import Any, Dict

from .errors import GuythonRuntimeError, GuythonSecurityError
from .constants import SAFE_FUNCTIONS, SAFE_OPERATIONS
from ..packages.GPD import GPD


class ExpressionEvaluator:
    """Safe expression evaluator"""
    
    def __init__(self, variables: Dict[str, Any], functions: Dict[str, Any]):
        self.variables = variables
        self.functions = functions
        self.gpd = GPD(self)
    
    def evaluate(self, expr: str) -> Any:
        """Handle function calls with arguments"""
        try:
            expr = re.sub(r'(\w+)_', r'\1()', expr)
            node = ast.parse(expr, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise GuythonRuntimeError(f"Error evaluating expression: {e}")
    
    def _evaluate_ast(self, expr: str) -> Any:
        """Evaluate expression using AST"""
        expr = expr.replace('^', '**')
        
        try:
            node = ast.parse(expr, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise GuythonRuntimeError(f"Invalid expression: {expr}")
    
    def _eval_node(self, node):
        """Handle function calls with arguments"""
        if isinstance(node, ast.Call):
            func = self._eval_node(node.func)
            args = [self._eval_node(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval_node(kw.value) for kw in node.keywords}
            
            if callable(func):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    raise GuythonRuntimeError(f"Error calling function: {e}")
            raise GuythonRuntimeError(f"Not callable: {func}")
        elif isinstance(node, ast.Attribute):
            # Handle attribute access (module.function)
            obj = self._eval_node(node.value)
            if hasattr(obj, node.attr):
                attr = getattr(obj, node.attr)
                if callable(attr):
                    # Return callable as-is - will be handled in ast.Call case
                    return attr
                else:
                    return attr
            else:
                raise GuythonRuntimeError(f"Attribute not found: {node.attr}")
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Constant):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Constant):  # Python < 3.8 compatibility
            return node.s
        elif isinstance(node, ast.Name):
            if node.id in self.variables:
                return self.variables[node.id]
            elif node.id in self.functions:
                return self.functions[node.id]
            else:
                raise GuythonRuntimeError(f"Undefined variable: {node.id}")
        elif isinstance(node, ast.Attribute):
            # Handle module.variable access
            obj = self._eval_node(node.value)
            if hasattr(obj, node.attr):
                return getattr(obj, node.attr)
            else:
                raise GuythonRuntimeError(f"Attribute '{node.attr}' not found")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_name = type(node.op).__name__
            
            # Map AST operators to our safe operations
            op_map = {
                'Add': '+', 'Sub': '-', 'Mult': '*', 'Div': '/', 'FloorDiv': '//',
                'Mod': '%', 'Pow': '**', 'Eq': '==', 'NotEq': '!=',
                'Lt': '<', 'LtE': '<=', 'Gt': '>', 'GtE': '>='
            }
            
            if op_name in op_map:
                op_func = SAFE_OPERATIONS[op_map[op_name]]
                return op_func(left, right)
            else:
                raise GuythonRuntimeError(f"Unsupported operation: {op_name}")
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left)
            result = True
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_name = type(op).__name__
                op_map = {
                    'Eq': '==', 'NotEq': '!=', 'Lt': '<', 'LtE': '<=',
                    'Gt': '>', 'GtE': '>='
                }
                if op_name in op_map:
                    op_func = SAFE_OPERATIONS[op_map[op_name]]
                    result = result and op_func(left, right)
                    left = right
                else:
                    raise GuythonRuntimeError(f"Unsupported comparison: {op_name}")
            return result
        elif isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else str(node.func)
            if func_name in SAFE_FUNCTIONS:
                args = [self._eval_node(arg) for arg in node.args]
                return SAFE_FUNCTIONS[func_name](*args)
            else:
                raise GuythonSecurityError(f"Function not allowed: {func_name}")
        elif isinstance(node, ast.Attribute):
            obj = self._eval_node(node.value)
            if hasattr(obj, node.attr):
                return getattr(obj, node.attr)
            else:
                raise GuythonRuntimeError(f"Attribute not found: {node.attr}")
        else:
            raise GuythonRuntimeError(f"Unsupported AST node: {type(node).__name__}")