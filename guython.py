import re
import math
import os
import sys
import ast
import operator
from types import SimpleNamespace
from typing import Dict, List, Tuple, Any, Optional, Union

# Version constant
VERSION = "v1.0.0b2536"

# Maximum iterations for loops to prevent infinite loops
MAX_LOOP_ITERATIONS = 10000

# Safe math operations
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

# Safe built-in functions
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

class GuythonError(Exception):
    """Base exception for Guython interpreter errors"""
    pass

class GuythonSyntaxError(GuythonError):
    """Syntax error in Guython code"""
    pass

class GuythonRuntimeError(GuythonError):
    """Runtime error in Guython code"""
    pass

class GuythonSecurityError(GuythonError):
    """Security-related error"""
    pass

class GuythonGotoException(Exception):
    """Exception used for goto control flow"""
    def __init__(self, target_line: int):
        self.target_line = target_line
        super().__init__(f"Goto line {target_line}")

class ExpressionEvaluator:
    """Safe expression evaluator="""
    
    def __init__(self, variables: Dict[str, Any], functions: Dict[str, Any]):
        self.variables = variables
        self.functions = functions
    
    def evaluate(self, expr: str) -> Any:
        """Safely evaluate an expression"""
        expr = expr.strip()
        if not expr:
            return None
        
        # Handle simple literals
        if expr.startswith('"') and expr.endswith('"'):
            return expr[1:-1]
        if expr.startswith("'") and expr.endswith("'"):
            return expr[1:-1]
        
        # Try to parse as a number
        try:
            if '.' in expr:
                return float(expr)
            return int(expr)
        except ValueError:
            pass
        
        # Handle variables
        if expr in self.variables:
            return self.variables[expr]
        
        # Handle simple module variables (e.g., module.variable) - only if no operators
        if '.' in expr and not any(op in expr for op in SAFE_OPERATIONS.keys()):
            parts = expr.split('.')
            if len(parts) == 2 and parts[0] in self.variables:
                module = self.variables[parts[0]]
                if hasattr(module, parts[1]):
                    return getattr(module, parts[1])
        
        # For complex expressions, use a limited AST evaluation
        try:
            return self._evaluate_ast(expr)
        except Exception as e:
            raise GuythonRuntimeError(f"Error evaluating expression '{expr}': {e}")
    
    def _evaluate_ast(self, expr: str) -> Any:
        """Evaluate expression using AST"""
        # Replace ^ with ** for Python compatibility
        expr = expr.replace('^', '**')
        
        try:
            node = ast.parse(expr, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise GuythonRuntimeError(f"Invalid expression: {expr}")
    
    def _eval_node(self, node) -> Any:
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):
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

class GuythonInterpreter:
    """Main Guython interpreter class"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, List[Tuple[int, str]]] = {}
        self.loop_stack: List[Tuple[str, int, List[Tuple[int, str]]]] = []
        self.if_stack: List[Tuple[bool, int]] = []
        self.defining_function: Optional[Tuple[str, int]] = None
        self.function_stack: List[Tuple[int, str]] = []
        self.current_line_number = 0
        self.debug_mode = False
        # New attributes for goto functionality
        self.program_lines: List[str] = []
        self.goto_max_jumps = 1000  # Prevent infinite goto loops
        self.goto_jump_count = 0
        
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode"""
        self.debug_mode = enabled
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug_mode:
            print(f"[DEBUG] {message}")
    
    def _strip_comments(self, line: str) -> str:
        """Remove comments from a line"""
        result = ''
        i = 0
        while i < len(line):
            if line[i] == '-':
                end = line.find('-', i + 1)
                if end != -1:
                    i = end + 1
                else:
                    break
            else:
                result += line[i]
                i += 1
        return result.strip()
    
    def _validate_variable_name(self, name: str) -> bool:
        """Validate variable name"""
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
            return False
        if name in SAFE_FUNCTIONS or name in ['import', 'print', 'if', 'while', 'def', 'goto']:
            return False
        return True
    
    def _get_indent_level(self, line: str) -> Tuple[int, str]:
        """Get indentation level and code"""
        indent = 0
        while indent < len(line) and line[indent] == '.':
            indent += 1
        return indent, line[indent:]
    
    def run_program(self, lines: List[str]):
        """Run a complete program with goto support"""
        self.program_lines = lines
        self.goto_jump_count = 0
        
        line_number = 0
        while line_number < len(lines):
            try:
                self.run_line(lines[line_number], line_number=line_number + 1)
                line_number += 1
            except GuythonGotoException as goto_ex:
                # Handle goto jump
                target_line = goto_ex.target_line
                if target_line < 1 or target_line > len(lines):
                    raise GuythonRuntimeError(f"Goto target line {target_line} is out of range (1-{len(lines)})")
                
                self.goto_jump_count += 1
                if self.goto_jump_count > self.goto_max_jumps:
                    raise GuythonRuntimeError(f"Maximum goto jumps exceeded ({self.goto_max_jumps}). Possible infinite loop.")
                
                line_number = target_line - 1  # Convert to 0-based index
                self._debug_print(f"Goto jump to line {target_line}")
        
        # Execute any remaining loops
        self.execute_remaining_loops()
    
    def run_line(self, line: str, importing: bool = False, line_number: int = 0):
        """Execute a single line of Guython code"""
        line = line.rstrip("\n")
        line = self._strip_comments(line)
        self.current_line_number = line_number
        
        if not line.strip():
            return
        
        try:
            indent, code = self._get_indent_level(line)
            self._debug_print(f"Line {line_number}: indent={indent}, code='{code}'")
            
            # Close blocks based on indentation
            self._close_blocks(indent)
            
            # Handle function definition
            if self.defining_function:
                if indent > self.defining_function[1]:
                    self.function_stack.append((indent, code))
                    return
                else:
                    self.functions[self.defining_function[0]] = self.function_stack
                    self.defining_function = None
                    self.function_stack = []
            
            # Process the command
            self._process_command(code, indent, importing)
            
        except GuythonGotoException:
            # Re-raise goto exceptions to be handled by run_program
            raise
        except GuythonError as e:
            if not importing:
                print(f"Error on line {line_number}: {e}")
        except Exception as e:
            if not importing:
                print(f"Unexpected error on line {line_number}: {e}")
    
    def _process_command(self, code: str, indent: int, importing: bool):
        """Process a single command"""

        # Function definition
        if code.startswith('def'):
            self._handle_function_definition(code, indent, importing)

        # Control flow
        elif code.startswith('while'):
            self._handle_while(code, indent, importing)

        elif code.startswith('if'):
            self._handle_if(code, indent, importing)

        # Add to loop block
        elif self.loop_stack and indent > self.loop_stack[-1][1]:
            self.loop_stack[-1][2].append((indent, code))

        # Skip if we're in a false if block - CHECK THIS BEFORE GOTO
        elif self.if_stack and not self.if_stack[-1][0] and indent > self.if_stack[-1][1]:
            self._debug_print(f"Skipping line due to false if condition: {code}")
            return

        # Goto statement - NOW checked after if-block logic
        elif code.startswith('goto'):
            self._handle_goto(code, importing)
            return

        # Import
        elif code.startswith("import"):
            self._handle_import(code, importing)


        # Function call
        elif code.endswith('_'):
            self._handle_function_call(code, importing)

        # Input operations - FIXED: Check these before general assignment
        elif code.startswith('printinput') or code.startswith('print input'):
            self._handle_print_input(importing)

        elif code.endswith('=input'):
            self._handle_input_assignment(code, importing)

        # Variable assignment - check this after input operations
        elif '=' in code and not code.startswith('print') and code != "5+5=4":
            self._handle_assignment(code, importing)

        # Print statement
        elif code.startswith('print'):
            self._handle_print(code, importing)

        # Easter eggs (these could be made optional)
        elif code == "5+5=4":
            if not importing:
                print("chatgpt actually said this bruh 😭")

        elif code == "9+10":
            if not importing:
                print("21")
                print("you stupid")
                print("its 19")

        elif code == "ver" and "=" not in code:
            if not importing:
                print("Guython", VERSION)

        # Expression evaluation
        else:
            if not importing:
                try:
                    evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                    result = evaluator.evaluate(code)
                    if result is not None:
                        print(result)
                except GuythonError:
                    raise
                except Exception as e:
                    raise GuythonRuntimeError(f"Error evaluating expression: {e}")
    
    def _handle_goto(self, code: str, importing: bool):
        """Handle goto statement"""
        # Extract line number from goto command
        # Handle both "goto 5" and "goto5" syntax
        if code.startswith('goto '):
            line_str = code[5:].strip()
        elif code.startswith('goto'):
            line_str = code[4:].strip()
        else:
            raise GuythonSyntaxError("Invalid goto syntax")

        if not line_str or not line_str.isdigit():
            raise GuythonSyntaxError("Goto syntax error. Use: goto<line_number> or goto <line_number> (e.g., goto5 or goto 5)")

        target_line = int(line_str)
        self._debug_print(f"Goto statement: jumping to line {target_line}")

        # Raise exception to trigger jump in run_program
        raise GuythonGotoException(target_line)
    
    def _handle_function_definition(self, code: str, indent: int, importing: bool):
        """Handle function definition"""
        match = re.match(r'^def(\w+)_$', code)
        if not match:
            raise GuythonSyntaxError("Invalid function definition syntax. Use: def<functionName>_")
        
        func_name = match.group(1)
        if not self._validate_variable_name(func_name):
            raise GuythonSyntaxError(f"Invalid function name: {func_name}")
            
        self.defining_function = (func_name, indent)
        self.function_stack = []
        self._debug_print(f"Defining function: {func_name}")
    
    def _handle_while(self, code: str, indent: int, importing: bool):
        """Handle while loop"""
        # Handle both "while condition" and "whilecondition" syntax
        if code.startswith('while '):
            condition = code[6:].strip()
        elif code.startswith('while'):
            condition = code[5:].strip()
        else:
            condition = ""
            
        if not condition:
            raise GuythonSyntaxError("While loop missing condition")
            
        self.loop_stack.append((condition, indent, []))
        self._debug_print(f"Starting while loop with condition: {condition}")
    
    def _handle_if(self, code: str, indent: int, importing: bool):
        """Handle if statement"""
        # Handle both "if condition" and "ifcondition" syntax  
        if code.startswith('if '):
            condition = code[3:].strip()
        elif code.startswith('if'):
            condition = code[2:].strip()
        else:
            condition = ""

        if not condition:
            raise GuythonSyntaxError("If statement missing condition")

        try:
            evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
            result = evaluator.evaluate(condition)
            is_true = bool(result)
            self.if_stack.append((is_true, indent))
            self._debug_print(f"If condition '{condition}' evaluated to: {is_true}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error in if condition: {e}")
    
    def _handle_import(self, code: str, importing: bool):
        """Handle import statement"""
        filename = code[6:].strip()
        
        if not (filename.endswith(".gy") or filename.endswith(".guy")):
            raise GuythonSyntaxError("Invalid file type: Given file must be .gy or .guy")
            
        if not os.path.isfile(filename):
            raise GuythonRuntimeError(f"Module file not found: {filename}")
            
        module_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Validate module name
        if not self._validate_variable_name(module_name):
            raise GuythonSyntaxError(f"Invalid module name: {module_name}")
            
        # Load variables from file safely
        module_vars = self._load_vars_from_file(filename)
        self.variables[module_name] = SimpleNamespace(**module_vars)
        self._debug_print(f"Imported module: {module_name}")
    
    def _handle_function_call(self, code: str, importing: bool):
        """Handle function call with proper variable scoping"""
        func_name = code[:-1]
        
        if func_name not in self.functions:
            raise GuythonRuntimeError(f"Function '{func_name}_' not defined")
            
        self._debug_print(f"Calling function: {func_name}")
        
        # Save current state
        saved_loop_stack = self.loop_stack.copy()
        saved_if_stack = self.if_stack.copy()
        
        # Reset stacks for function execution
        self.loop_stack = []
        self.if_stack = []
        
        try:
            # Execute function body
            for fi, fline in self.functions[func_name]:
                self.run_line('.' * fi + fline, importing)
            
            # Execute any remaining loops from the function
            self.execute_remaining_loops()
            
        finally:
            # Restore previous state
            self.loop_stack = saved_loop_stack
            self.if_stack = saved_if_stack
    
    def _handle_assignment(self, code: str, importing: bool):
        """Handle variable assignment"""
        parts = code.split('=', 1)
        if len(parts) != 2:
            raise GuythonSyntaxError("Invalid assignment syntax")
            
        var_name = parts[0].strip()
        expr = parts[1].strip()
        
        if not self._validate_variable_name(var_name):
            raise GuythonSyntaxError(f"Invalid variable name: '{var_name}'")
            
        try:
            evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
            value = evaluator.evaluate(expr)
            self.variables[var_name] = value
            self._debug_print(f"Assigned {var_name} = {value}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error in assignment: {e}")
    
    def _handle_print(self, code: str, importing: bool):
        """Handle print statement"""
        if importing:
            return
            
        rest = code[5:].strip()
        if not rest:
            print()
            return
            
        # Split by commas outside quotes
        chunks = self._split_outside_quotes(rest, ',')
        output_parts = []
        
        for chunk in chunks:
            chunk = chunk.strip()
            tokens = self._tokenize_print_args(chunk)
            piece = ''
            
            for token in tokens:
                token = token.strip()
                if (token.startswith('"') and token.endswith('"')) or \
                   (token.startswith("'") and token.endswith("'")):
                    piece += token[1:-1]
                else:
                    try:
                        evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                        value = evaluator.evaluate(token)
                        piece += str(value)
                    except:
                        piece += '[Error]'
            
            output_parts.append(piece)
        
        print(' '.join(output_parts))
    
    def _handle_print_input(self, importing: bool):
        """Handle printinput command - FIXED"""
        if not importing:
            try:
                user_input = input()
                print(user_input)
                self._debug_print(f"Print input: {user_input}")
            except EOFError:
                print()  # Handle EOF gracefully
            except KeyboardInterrupt:
                raise  # Let keyboard interrupt propagate
    
    def _handle_input_assignment(self, code: str, importing: bool):
        """Handle input assignment - FIXED"""
        var_name = code[:-6].strip()  # Remove '=input'

        if not self._validate_variable_name(var_name):
            raise GuythonSyntaxError(f"Invalid variable name: '{var_name}'")

        if not importing:
            try:
                user_input = input()
                # Always try to convert to number if possible for better comparisons
                try:
                    # Try integer first
                    if '.' not in user_input and user_input.lstrip('-').isdigit():
                        self.variables[var_name] = int(user_input)
                    elif user_input.replace('.', '').replace('-', '').isdigit():
                        self.variables[var_name] = float(user_input)
                    else:
                        # Keep as string if not a number
                        self.variables[var_name] = user_input
                except ValueError:
                    # Keep as string if conversion fails
                    self.variables[var_name] = user_input

                self._debug_print(f"Input assigned to {var_name}: {self.variables[var_name]} (type: {type(self.variables[var_name]).__name__})")
            except EOFError:
                self.variables[var_name] = ""  # Handle EOF gracefully
            except KeyboardInterrupt:
                raise  # Let keyboard interrupt propagate
    
    def _load_vars_from_file(self, filename: str) -> Dict[str, Any]:
        """Load variables from a Guython file without executing code"""
        vars_dict = {}
        
        try:
            with open(filename, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = self._strip_comments(line).strip()
                    
                    # Skip empty lines and non-assignment statements
                    if not line or line.startswith(('def', 'while', 'if', 'print', 'import', 'goto')):
                        continue
                        
                    if '=' in line and not line.endswith('=input'):
                        parts = line.split('=', 1)
                        var_name = parts[0].strip()
                        expr = parts[1].strip()
                        
                        if self._validate_variable_name(var_name):
                            try:
                                evaluator = ExpressionEvaluator({}, SAFE_FUNCTIONS)
                                value = evaluator.evaluate(expr)
                                vars_dict[var_name] = value
                            except:
                                self._debug_print(f"Skipped invalid assignment on line {line_num}: {line}")
                                
        except IOError as e:
            raise GuythonRuntimeError(f"Error reading file {filename}: {e}")
            
        return vars_dict
    
    def _split_outside_quotes(self, s: str, delimiter: str) -> List[str]:
        """Split string by delimiter, ignoring delimiters inside quotes"""
        result = []
        current = ''
        in_single = False
        in_double = False
        
        for c in s:
            if c == "'" and not in_double:
                in_single = not in_single
                current += c
            elif c == '"' and not in_single:
                in_double = not in_double
                current += c
            elif c == delimiter and not in_single and not in_double:
                result.append(current)
                current = ''
            else:
                current += c
                
        result.append(current)
        return result
    
    def _tokenize_print_args(self, args_str: str) -> List[str]:
        """Tokenize print arguments"""
        tokens = []
        current = ''
        in_single = False
        in_double = False
        i = 0
        
        while i < len(args_str):
            c = args_str[i]
            
            if c == "'" and not in_double:
                if in_single:
                    current += c
                    tokens.append(current)
                    current = ''
                    in_single = False
                else:
                    if current:
                        tokens.append(current)
                        current = ''
                    current = c
                    in_single = True
                    
            elif c == '"' and not in_single:
                if in_double:
                    current += c
                    tokens.append(current)
                    current = ''
                    in_double = False
                else:
                    if current:
                        tokens.append(current)
                        current = ''
                    current = c
                    in_double = True
                    
            elif c == ' ' and not in_single and not in_double:
                if current:
                    tokens.append(current)
                    current = ''
                    
            else:
                current += c
                
            i += 1
            
        if current:
            tokens.append(current)
            
        return tokens
    
    def _close_blocks(self, indent: int):
        """Close blocks based on indentation level"""
        # Close if blocks
        while self.if_stack and self.if_stack[-1][1] >= indent:
            closed_if = self.if_stack.pop()
            self._debug_print(f"Closed if block: was_active={closed_if[0]}, indent={closed_if[1]}")

        # Execute and close while loops
        while self.loop_stack and self.loop_stack[-1][1] >= indent:
            condition, level, block = self.loop_stack.pop()
            self._execute_loop(condition, block)
    
    def _execute_loop(self, condition: str, block: List[Tuple[int, str]]):
        """Execute a while loop with safety measures"""
        iteration_count = 0
        evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
        
        try:
            while evaluator.evaluate(condition):
                if iteration_count >= MAX_LOOP_ITERATIONS:
                    raise GuythonRuntimeError(f"Loop exceeded maximum iterations ({MAX_LOOP_ITERATIONS})")
                    
                for block_indent, block_line in block:
                    self.run_line('.' * block_indent + block_line)
                    
                iteration_count += 1
                
                # Re-create evaluator to get updated variables
                evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                
        except GuythonError:
            raise
        except Exception as e:
            raise GuythonRuntimeError(f"Error in while loop: {e}")
    
    def execute_remaining_loops(self):
        """Execute any remaining loops at the end of the program"""
        while self.loop_stack:
            condition, level, block = self.loop_stack.pop()
            self._execute_loop(condition, block)
    
    def get_variables(self) -> Dict[str, Any]:
        """Get current variables (for debugging)"""
        return self.variables.copy()
    
    def get_functions(self) -> Dict[str, List[Tuple[int, str]]]:
        """Get defined functions (for debugging)"""
        return self.functions.copy()

def main():
    """Main entry point"""
    interpreter = GuythonInterpreter()
    
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        
        # Check for debug flag
        debug_mode = '--debug' in sys.argv
        if debug_mode:
            interpreter.set_debug_mode(True)
            sys.argv.remove('--debug')
        
        if not (filename.endswith('.gy') or filename.endswith('.guy')):
            print("Error: Invalid file type. Given file must be .gy or .guy")
            sys.exit(1)
            
        if not os.path.isfile(filename):
            print(f"Error: File not found: {filename}")
            sys.exit(1)
            
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                interpreter.run_program(lines)
        except Exception as e:
            print(f"Fatal error: {e}")
            sys.exit(1)
    else:
        # Interactive mode
        print(f"Guython Interpreter {VERSION}")
        print("Type 'exit' to quit, 'debug' to toggle debug mode, 'vars' to show variables.")
        
        while True:
            try:
                line = input(">>> ").strip()
                if line.lower() == 'exit':
                    break
                elif line.lower() == 'debug':
                    interpreter.set_debug_mode(not interpreter.debug_mode)
                    print(f"Debug mode: {'ON' if interpreter.debug_mode else 'OFF'}")
                    continue
                elif line.lower() == 'vars':
                    variables = interpreter.get_variables()
                    if variables:
                        for name, value in variables.items():
                            print(f"  {name} = {value}")
                    else:
                        print("  No variables defined")
                    continue
                elif line.startswith("guython "):
                    filename = line[8:].strip()
                    if not (filename.endswith('.gy') or filename.endswith('.guy')):
                        print("Error: Invalid file type. Given file must be .gy or .guy")
                        continue
                    if not os.path.isfile(filename):
                        print(f"Error: File not found: {filename}")
                        continue
                    try:
                        with open(filename, 'r') as f:
                            lines = f.readlines()
                            interpreter.run_program(lines)
                    except Exception as e:
                        print(f"Error executing file: {e}")
                    continue
                
                interpreter.run_line(line)
                interpreter.execute_remaining_loops()
                
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt: Use 'exit' to quit.")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == '__main__':
    main()
