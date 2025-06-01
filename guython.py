import re
import math
import sys
import os

ver = "v0.1 b2516."

class GuythonInterpreter:
    def __init__(self):
        self.variables = {}
        self.safe_globals = {
            'sqrt': math.sqrt,
            '__builtins__': {}
        }
        self.loop_stack = []
        self.if_stack = []
        self.modules = {}  # For imported modules

    def run_line(self, line):
        line = line.rstrip("\n")
        if not line.strip():
            return

        indent = len(line) - len(line.lstrip())
        line = line.strip()

        # Internal command to run a .gy file: guython filename.gy
        if line.startswith("guython "):
            _, filename = line.split(" ", 1)
            filename = filename.strip()
            if not filename.endswith(".gy") and not filename.endswith(".guy"):
                print("Invalid File Type: Given file must be .gy or .guy")
                return
            if not os.path.isfile(filename):
                print(f"File not found: {filename}")
                return
            with open(filename, 'r') as f:
                for subline in f:
                    self.run_line(subline)
                self.execute_loops()
            return

        # Adjust control stacks based on indentation
        while self.if_stack and self.if_stack[-1][1] >= indent:
            self.if_stack.pop()
        while self.loop_stack and self.loop_stack[-1][1] >= indent:
            self.loop_stack.pop()

        # Easter eggs
        if line == "5+5=4":
            print("bruh")
            return
        if line == "9+10":
            print("21")
            print("you stupid")
            print("its 19")
            return
        if line == "ver":
            print(f"Guython Interpreter {ver}")
            return

        # Input shortcut
        if line.startswith("printinput") or line.startswith("print input"):
            user_input = input()
            print(user_input)
            return

        # Input assignment
        if line.endswith("=input"):
            var_name = line[:-6].strip()
            if var_name in dir(__builtins__) or var_name in self.safe_globals:
                print(f"Invalid variable name: '{var_name}' is a reserved name")
                return
            user_input = input()
            self.variables[var_name] = user_input
            return

        # If-statement
        if line.startswith("if"):
            condition = line[2:].strip()
            try:
                result = self._evaluate_expression(condition)
                self.if_stack.append((bool(result), indent))
            except Exception as e:
                print(f"Error in if condition: {e}")
            return

        # While-statement
        if line.startswith("while"):
            condition = line[5:].strip()
            self.loop_stack.append((condition, indent, []))
            return

        # Add lines to loop block
        if self.loop_stack:
            self.loop_stack[-1][2].append((indent, line))
            return

        # Only execute if not inside false if block
        if all(active for active, _ in self.if_stack):
            self._process_line(line)

    def _process_line(self, line):
        # Handle import (e.g., importguy.gy or import guy.gy)
        import_match = re.match(r'import(?:guy\.gy)?\s*(.+)', line) or re.match(r'import guy\.guy\s*(.+)', line)
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

        # Variable assignment
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

        # Print statement with comma-based spacing
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

                output_chunks.append(''.join(chunk_parts))  # no space inside chunk

            print(' '.join(output_chunks))  # space between comma-separated chunks

        # Expression line
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
        if not filename.endswith('.gy') and not filename.endswith('.guy'):
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
        print("Guython Interpreter", ver, "Type 'exit' to quit.")
        while True:
            try:
                line = input(">>> ")
                if line.strip().lower() == 'exit':
                    break
                interpreter.run_line(line)
                interpreter.execute_loops()
            except Exception as e:
                print(e)
