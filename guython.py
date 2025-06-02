import re
import math
import os
import sys
from types import SimpleNamespace

ver = "v0.2.2b2526."

class GuythonInterpreter:
    def __init__(self):
        self.variables = {}
        self.safe_globals = {
            'sqrt': math.sqrt,
            '__builtins__': {}
        }
        self.loop_stack = []
        self.if_stack = []
        self.functions = {}
        self.defining_function = None
        self.function_stack = []

    def _strip_comments(self, line):
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

    def run_line(self, line, importing=False):
        line = line.rstrip("\n")
        line = self._strip_comments(line)
        if not line.strip():
            return

        indent = 0
        while indent < len(line) and line[indent] == '.':
            indent += 1
        code = line[indent:]

        self._close_blocks(indent)

        if self.defining_function:
            if indent > self.defining_function[1]:
                self.function_stack.append((indent, code))
                return
            else:
                self.functions[self.defining_function[0]] = self.function_stack
                self.defining_function = None
                self.function_stack = []

        if code.startswith('def'):
            m = re.match(r'def(\w+)_', code)
            if m:
                func_name = m.group(1)
                self.defining_function = (func_name, indent)
                self.function_stack = []
                return
            if not importing:
                print("Invalid function definition syntax")
            return

        if code.startswith('while'):
            condition = code[5:]
            self.loop_stack.append((condition, indent, []))
            return

        if code.startswith('if'):
            condition = code[2:]
            try:
                result = self._evaluate_expression(condition)
                self.if_stack.append((bool(result), indent))
            except Exception as e:
                if not importing:
                    print(f"Error in if condition: {e}")
            return

        if self.loop_stack and indent > self.loop_stack[-1][1]:
            self.loop_stack[-1][2].append((indent, code))
            return

        if any(not active for active, _ in self.if_stack):
            return

        if code.startswith("import"):
            filename = code[6:].strip()
            if filename.endswith(".gy") or filename.endswith(".guy"):
                if not os.path.isfile(filename):
                    if not importing:
                        print(f"Module file not found: {filename}")
                    return
                module_name = os.path.splitext(os.path.basename(filename))[0]
                # Load variables by parsing only assignments, no code execution
                module_vars = self._load_vars_from_file(filename)
                self.variables[module_name] = SimpleNamespace(**module_vars)
            else:
                if not importing:
                    print("Invalid File Type: Given file must be .gy or .guy")
            return

        if code.endswith('_'):
            func_name = code[:-1]
            if func_name in self.functions:
                for fi, fline in self.functions[func_name]:
                    self.run_line('.' * fi + fline)
            else:
                if not importing:
                    print(f"Function '{func_name}_' not defined")
            return

        if '=' in code and not code.startswith('print'):
            parts = code.split('=', 1)
            var_name = parts[0].strip()
            if var_name in dir(__builtins__) or var_name in self.safe_globals:
                if not importing:
                    print(f"Invalid variable name: '{var_name}' is reserved")
                return
            expr = parts[1].strip()
            try:
                value = self._evaluate_expression(expr)
                self.variables[var_name] = value
            except Exception as e:
                if not importing:
                    print(f"Error in assignment: {e}")
            return

        if code.startswith('print'):
            rest = code[5:]
            self._handle_print(rest)
            return

        if code.startswith('printinput') or code.startswith('print input'):
            if not importing:
                user_input = input()
                print(user_input)
            return

        if code.endswith('=input'):
            var_name = code[:-6]
            if var_name in dir(__builtins__) or var_name in self.safe_globals:
                if not importing:
                    print(f"Invalid variable name: '{var_name}' is reserved")
                return
            if not importing:
                user_input = input()
                self.variables[var_name] = user_input
            return

        if code == "5+5=4":
            if not importing:
                print("bruh")
            return
        if code == "9+10":
            if not importing:
                print("21")
                print("you stupid")
                print("its 19")
            return
        if code == "ver'" and "=" not in code:
            if not importing:
                print("Guython", ver)

        if not importing:
            try:
                res = self._evaluate_expression(code)
                if res is not None:
                    print(res)
            except Exception as e:
                print(f"Error: {e}")

    def _load_vars_from_file(self, filename):
        vars_dict = {}
        with open(filename, 'r') as f:
            for line in f:
                line = self._strip_comments(line).strip()
                if not line or line.startswith('def') or line.startswith('while') or line.startswith('if') or line.startswith('print') or line.startswith('import'):
                    continue
                if '=' in line:
                    parts = line.split('=', 1)
                    var_name = parts[0].strip()
                    expr = parts[1].strip()
                    if var_name and re.match(r'^[A-Za-z_]\w*$', var_name):
                        try:
                            val = self._evaluate_expression(expr)
                            vars_dict[var_name] = val
                        except:
                            pass  # ignore lines with errors silently
        return vars_dict

    def _handle_print(self, rest):
        rest = rest.strip()
        if not rest:
            print()
            return
        chunks = self._split_outside_quotes(rest, ',')
        out_chunks = []
        for chunk in chunks:
            chunk = chunk.strip()
            tokens = self._tokenize_print_args(chunk)
            piece = ''
            for t in tokens:
                t = t.strip()
                if (t.startswith('"') and t.endswith('"')) or (t.startswith("'") and t.endswith("'")):
                    piece += t[1:-1]
                else:
                    try:
                        val = self._evaluate_expression(t)
                        piece += str(val)
                    except:
                        piece += '[Error]'
            out_chunks.append(piece)
        print(' '.join(out_chunks))

    def _split_outside_quotes(self, s, delimiter):
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

    def _tokenize_print_args(self, args_str):
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
                i += 1
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
                i += 1
            elif c == ' ' and not in_single and not in_double:
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

    def _evaluate_expression(self, expr):
        expr = expr.replace('^', '**')
        local_vars = self.variables.copy()
        try:
            return eval(expr, self.safe_globals, local_vars)
        except Exception as e:
            raise e

    def _close_blocks(self, indent):
        while self.if_stack and self.if_stack[-1][1] >= indent:
            self.if_stack.pop()
        while self.loop_stack and self.loop_stack[-1][1] >= indent:
            condition, lvl, block = self.loop_stack.pop()
            try:
                while self._evaluate_expression(condition):
                    for bl_indent, bl_line in block:
                        self.run_line('.' * bl_indent + bl_line)
            except Exception as e:
                print(f"Error in while loop: {e}")

    def execute_remaining_loops(self):
        while self.loop_stack:
            condition, lvl, block = self.loop_stack.pop()
            try:
                while self._evaluate_expression(condition):
                    for bl_indent, bl_line in block:
                        self.run_line('.' * bl_indent + bl_line)
            except Exception as e:
                print(f"Error in while loop: {e}")

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
        with open(filename, 'r') as f:
            for line in f:
                interpreter.run_line(line)
            interpreter.execute_remaining_loops()
    else:
        print("Guython Interpreter", ver, "Type 'exit' to quit.")
        while True:
            try:
                line = input(">>> ").strip()
                if line.lower() == 'exit':
                    break
                if line.startswith("guython "):
                    filename = line[8:].strip()
                    if not (filename.endswith('.gy') or filename.endswith('.guy')):
                        print("Invalid File Type: Given file must be .gy or .guy")
                        continue
                    if not os.path.isfile(filename):
                        print(f"File not found: {filename}")
                        continue
                    with open(filename, 'r') as f:
                        for file_line in f:
                            interpreter.run_line(file_line)
                        interpreter.execute_remaining_loops()
                    continue
                interpreter.run_line(line)
                interpreter.execute_remaining_loops()
            except Exception as e:
                print(e)

