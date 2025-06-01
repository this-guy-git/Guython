import re
import math
import sys
import os

class GuythonInterpreter:
    def __init__(self):
        self.variables = {}
        self.safe_globals = {
            'sqrt': math.sqrt,
            '__builtins__': {}
        }
        self.loop_stack = []
        self.if_stack = []
        self.modules = {}
        self.functions = {}
        self.defining_function = None
        self.function_stack = []

    def _strip_comments(self, line):
        result = ''
        in_comment = False
        i = 0
        while i < len(line):
            if not in_comment and line[i] == '-':
                end = line.find('-', i + 1)
                if end != -1:
                    i = end + 1
                else:
                    break
            else:
                result += line[i]
                i += 1
        return result.strip()

    def run_line(self, line):
        line = line.rstrip("\n")
        line = self._strip_comments(line)
        if not line.strip():
            return

        indent = len(line) - len(line.lstrip())
        line = line.strip()

        while self.if_stack and self.if_stack[-1][1] >= indent:
            self.if_stack.pop()
        while self.loop_stack and self.loop_stack[-1][1] >= indent:
            self.loop_stack.pop()
        if self.defining_function and indent <= self.defining_function[1]:
            self.functions[self.defining_function[0]] = self.function_stack
            self.defining_function = None
            self.function_stack = []

        if line == "5+5=4":
            print("bruh")
            return
        if line == "9+10":
            print("21")
            print("you stupid")
            print("its 19")
            return

        if line.startswith("printinput") or line.startswith("print input"):
            user_input = input()
            print(user_input)
            return

        if line.endswith("=input"):
            var_name = line[:-6].strip()
            if var_name in dir(__builtins__) or var_name in self.safe_globals:
                print(f"Invalid variable name: '{var_name}' is a reserved name")
                return
            user_input = input()
            self.variables[var_name] = user_input
            return

        if line.startswith("def"):
            match = re.match(r'def\s*(\w+)_\s*', line)
            if match:
                func_name = match.group(1)
                self.defining_function = (func_name, indent)
                self.function_stack = []
            else:
                print("Invalid function definition. Function name must end with '_'")
            return

        if self.defining_function:
            self.function_stack.append((indent, line))
            return

        if line.startswith("if"):
            condition = line[2:].strip()
            try:
                result = self._evaluate_expression(condition)
                self.if_stack.append((bool(result), indent))
            except Exception as e:
                print(f"Error in if condition: {e}")
            return

        if line.startswith("while"):
            condition = line[5:].strip()
            self.loop_stack.append((condition, indent, []))
            return

        if self.loop_stack:
            self.loop_stack[-1][2].append((indent, line))
            return

        if all(active for active, _ in self.if_stack):
            self._process_line(line)

    def _process_line(self, line):
        if line.startswith("import"):
            import_match = re.match(r'import\s*(.+)', line)
            if import_match:
                filename = import_match.group(1).strip()
                if filename.endswith(".gy") or filename.endswith(".guy"):
                    module_name = os.path.splitext(os.path.basename(filename))[0]
                    module_interpreter = GuythonInterpreter()
                    if not os.path.isfile(filename):
                        print(f"Module file not found: {filename}")
                        return
                    with open(filename, 'r') as f:
                        for module_line in f:
                            module_line = module_line.strip()
                            if '=' in module_line and not module_line.startswith('print'):
                                module_interpreter.run_line(module_line)
                    self.variables[module_name] = module_interpreter.variables
                else:
                    print("Invalid File Type: Given file must be .gy or .guy")
            return

        if line.endswith("_"):
            func_name = line[:-1]
            if func_name in self.functions:
                for blk_indent, blk_line in self.functions[func_name]:
                    self.run_line(' ' * blk_indent + blk_line)
            else:
                print(f"Function '{func_name}_' not defined")
            return

        if '=' in line and not line.startswith('print'):
            var_match = re.match(r'(\w+)\s*=\s*(.+)', line)
            if var_match:
                var_name = var_match.group(1)
                if var_name in dir(__builtins__) or var_name in self.safe_globals:
                    print(f"Invalid variable name: '{var_name}' is a reserved name")
                    return
                value_expr = var_match.group(2)
                try:
                    value = self._evaluate_expression(value_expr)
                    self.variables[var_name] = value
                except Exception as e:
                    print(f"Error in assignment: {e}")
            else:
                print("Invalid assignment syntax.")

        elif line.startswith('print'):
            args_str = line[len('print'):].lstrip()
            if not args_str:
                print()
                return

            chunks = self._split_outside_quotes(args_str, ',')

            output_chunks = []
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue

                tokens = self._tokenize_print_args(chunk)
                chunk_parts = []
                for token in tokens:
                    token = token.strip()
                    if (token.startswith('"') and token.endswith('"')) or \
                       (token.startswith("'") and token.endswith("'")):
                        chunk_parts.append(token[1:-1])
                    else:
                        try:
                            val = self._evaluate_expression(token)
                            chunk_parts.append(str(val))
                        except Exception as e:
                            chunk_parts.append(f"[Error: {e}]")

                output_chunks.append(''.join(chunk_parts))

            print(' '.join(output_chunks))

        else:
            try:
                result = self._evaluate_expression(line)
                print(result)
            except Exception as e:
                print(f"Error: {e}")

    def _tokenize_print_args(self, args_str):
        tokens = []
        current = ''
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(args_str):
            c = args_str[i]
            if c == "'" and not in_double_quote:
                if in_single_quote:
                    current += c
                    tokens.append(current)
                    current = ''
                    in_single_quote = False
                else:
                    if current:
                        tokens.append(current)
                        current = ''
                    current = c
                    in_single_quote = True
                i += 1
            elif c == '"' and not in_single_quote:
                if in_double_quote:
                    current += c
                    tokens.append(current)
                    current = ''
                    in_double_quote = False
                else:
                    if current:
                        tokens.append(current)
                        current = ''
                    current = c
                    in_double_quote = True
                i += 1
            elif c == ' ' and not in_single_quote and not in_double_quote:
                if current:
                    tokens.append(current)
                    current = ''
                i += 1
            else:
                current += c
                i += 1
        if current:
            tokens.append(current)
        return tokens

    def _split_outside_quotes(self, s, delimiter):
        result = []
        current = ''
        in_single_quote = False
        in_double_quote = False
        for c in s:
            if c == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current += c
            elif c == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current += c
            elif c == delimiter and not in_single_quote and not in_double_quote:
                result.append(current)
                current = ''
            else:
                current += c
        result.append(current)
        return result

    def _evaluate_expression(self, expr):
        expr = expr.strip()
        expr = expr.replace('^', '**')

        if expr == "5+5=4":
            raise ValueError("bruh")

        tokens = re.findall(r'\b\w+(?:\.\w+)?\b', expr)
        for token in tokens:
            if '.' in token:
                module, attr = token.split('.', 1)
                if module in self.variables and isinstance(self.variables[module], dict):
                    if attr in self.variables[module]:
                        value = self.variables[module][attr]
                        expr = expr.replace(token, str(value))
                    else:
                        raise ValueError(f"'{module}' has no attribute '{attr}'")
            elif token in self.variables:
                expr = re.sub(r'\b' + re.escape(token) + r'\b', str(self.variables[token]), expr)

        return eval(expr, self.safe_globals)

    def execute_loops(self):
        for condition, indent, block in self.loop_stack:
            while True:
                try:
                    if not self._evaluate_expression(condition):
                        break
                    for blk_indent, blk_line in block:
                        self.run_line(' ' * blk_indent + blk_line)
                except Exception as e:
                    print(f"Error in while loop: {e}")
                    break
        self.loop_stack.clear()

if __name__ == '__main__':
    interpreter = GuythonInterpreter()

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if not (filename.endswith('.gy') or filename.endswith('.guy')):
            print("Invalid File Type: Given file must be .gy or .guy")
            sys.exit(1)
        if not os.path.isfile(filename):
            print(f"File not found: {filename}")
            sys.exit(1)
        with open(filename, 'r') as file:
            for line in file:
                interpreter.run_line(line)
            interpreter.execute_loops()
    else:
        print("Guython Interpreter. Type 'exit' to quit.")
        while True:
            try:
                line = input(">>> ")
                if line.strip().lower() == 'exit':
                    break
                interpreter.run_line(line)
                interpreter.execute_loops()
            except Exception as e:
                print(e)
