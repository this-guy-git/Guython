import os
import re
from types import SimpleNamespace
from typing import Dict, List, Tuple, Any, Optional
import sys

from .errors import (
    GuythonError,
    GuythonSyntaxError,
    GuythonRuntimeError,
    GuythonSecurityError,
    GuythonGotoException,
)
from .constants import VERSION, MAX_LOOP_ITERATIONS, SAFE_FUNCTIONS
from .evaluator import ExpressionEvaluator
from .gui import GuythonGUI
from ..packages.GPD import GPD


class GuythonInterpreter:
    """Main Guython interpreter class"""

    import os
    import sys
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.functions: Dict[str, List[Tuple[int, str]]] = {}
        self.loop_stack: List[Tuple[str, int, List[Tuple[int, str]]]] = []
        self.if_stack: List[Tuple[bool, int]] = []
        self.defining_function: Optional[Tuple[str, int]] = None
        self.function_stack: List[Tuple[int, str]] = []
        self.current_line_number = 0
        self.debug_mode = False
        self.program_lines: List[str] = []
        self.goto_max_jumps = 1000  # Prevent infinite goto loops
        self.goto_jump_count = 0
        self.gui = GuythonGUI(interpreter=self)
        self.gpd = GPD(self)
        self.functions = {}
        self.aliases = {}
        self.else_stack = []
        
        # New features
        self.last_output = None  # Store last printed value for '_' variable
        
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
            if line[i] == '{':
                end = line.find('}', i + 1)
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
        if name in SAFE_FUNCTIONS or name in ['import', 'print', 'if', 'while', 'def', 'goto', 'eval']:
            return False
        return True
    
    def _get_indent_level(self, line: str) -> Tuple[int, str]:
        """Get indentation level and code"""
        indent = 0
        while indent < len(line) and line[indent] == '.':
            indent += 1
        return indent, line[indent:]
    
    def _parse_array_literal(self, expr: str) -> List[Any]:
        """Parse array literal like [1,2,3] or ['a','b','c']"""
        if not (expr.startswith('[') and expr.endswith(']')):
            raise GuythonSyntaxError("Invalid array syntax")
        
        content = expr[1:-1].strip()
        if not content:
            return []
        
        # Split by commas, respecting quotes
        elements = self._split_outside_quotes(content, ',')
        result = []
        evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
        
        for element in elements:
            element = element.strip()
            if element:
                try:
                    value = evaluator.evaluate(element)
                    result.append(value)
                except Exception as e:
                    raise GuythonRuntimeError(f"Error evaluating array element '{element}': {e}")
        
        return result
    
    def _handle_array_access(self, code: str) -> Any:
        """Handle array access like x[0] or nested like x[0][1]"""
        # Find the variable name and indices
        bracket_start = code.find('[')
        if bracket_start == -1:
            raise GuythonSyntaxError("Invalid array access syntax")
        
        var_name = code[:bracket_start].strip()
        if var_name not in self.variables:
            raise GuythonRuntimeError(f"Variable '{var_name}' not found")
        
        current_value = self.variables[var_name]
        remaining = code[bracket_start:]
        
        # Parse all bracket accesses
        evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
        while remaining.startswith('['):
            end_bracket = remaining.find(']')
            if end_bracket == -1:
                raise GuythonSyntaxError("Missing closing bracket")
            
            index_expr = remaining[1:end_bracket]
            try:
                index = evaluator.evaluate(index_expr)
                if not isinstance(index, int):
                    raise GuythonRuntimeError(f"Array index must be integer, got {type(index).__name__}")
                
                if not isinstance(current_value, list):
                    raise GuythonRuntimeError(f"Cannot index non-array value of type {type(current_value).__name__}")
                
                if index < 0 or index >= len(current_value):
                    raise GuythonRuntimeError(f"Array index {index} out of bounds (0-{len(current_value)-1})")
                
                current_value = current_value[index]
                remaining = remaining[end_bracket + 1:]
                
            except GuythonError:
                raise
            except Exception as e:
                raise GuythonRuntimeError(f"Error accessing array index: {e}")
        
        return current_value
    
    def _handle_array_assignment(self, var_part: str, value: Any):
        """Handle array element assignment like x[0] = 5"""
        bracket_start = var_part.find('[')
        if bracket_start == -1:
            raise GuythonSyntaxError("Invalid array assignment syntax")
        
        var_name = var_part[:bracket_start].strip()
        if var_name not in self.variables:
            raise GuythonRuntimeError(f"Variable '{var_name}' not found")
        
        if not isinstance(self.variables[var_name], list):
            raise GuythonRuntimeError(f"Cannot assign to index of non-array variable '{var_name}'")
        
        # For simplicity, only handle single-level indexing for assignment
        bracket_end = var_part.find(']')
        if bracket_end == -1:
            raise GuythonSyntaxError("Missing closing bracket")
        
        index_expr = var_part[bracket_start + 1:bracket_end]
        try:
            evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
            index = evaluator.evaluate(index_expr)
            
            if not isinstance(index, int):
                raise GuythonRuntimeError(f"Array index must be integer, got {type(index).__name__}")
            
            array = self.variables[var_name]
            if index < 0 or index >= len(array):
                raise GuythonRuntimeError(f"Array index {index} out of bounds (0-{len(array)-1})")
            
            array[index] = value
            self._debug_print(f"Set {var_name}[{index}] = {value}")
            
        except GuythonError:
            raise
        except Exception as e:
            raise GuythonRuntimeError(f"Error in array assignment: {e}")
    
    def _handle_eval_command(self, code: str, importing: bool):
        """Handle eval command to execute Guython code from string"""
        if importing:
            return
        
        # Extract the expression to evaluate
        expr = code[4:].strip()  # Remove 'eval' prefix
        
        try:
            evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
            code_to_execute = evaluator.evaluate(expr)
            
            if not isinstance(code_to_execute, str):
                raise GuythonRuntimeError(f"Eval requires string argument, got {type(code_to_execute).__name__}")
            
            self._debug_print(f"Evaluating code: {code_to_execute}")
            
            # Execute the code
            self.run_line(code_to_execute, importing=False, line_number=self.current_line_number)
            
        except GuythonError:
            raise
        except Exception as e:
            raise GuythonRuntimeError(f"Error in eval: {e}")
    
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
        original_line = line  # Keep original for debugging
        line = self._strip_comments(line)
        self.current_line_number = line_number

        if not line.strip():
            return

        try:
            indent, code = self._get_indent_level(line)
            #print(f"DEBUG: Line {line_number}: indent={indent}, code='{code}', defining_function={self.defining_function}")

            # Handle function definition body collection FIRST
            if self.defining_function:
                func_name, func_indent = self.defining_function
                #print(f"DEBUG: In function definition mode for '{func_name}', func_indent={func_indent}, current_indent={indent}")

                if indent > func_indent:
                    # This line is part of the function body
                    self.function_stack.append((indent, code))
                    #print(f"DEBUG: Added to function body: ({indent}, '{code}')")
                    return
                else:
                    # Function definition is complete
                    self.functions[func_name]['body'] = self.function_stack.copy()
                    #print(f"DEBUG: Function '{func_name}' body complete: {self.function_stack}")
                    self.defining_function = None
                    self.function_stack = []
                    # IMPORTANT: Continue processing the current line normally
                    # Don't return here - let it fall through to _process_command

            # Close blocks based on indentation
            self._close_blocks(indent)

            # Process the command
            self._process_command(code, indent, importing)

        except GuythonGotoException:
            # Re-raise goto exceptions to be handled by run_program
            raise
        except GuythonError as e:
            if not importing:
                stripped_line = original_line.rstrip('\n')
                first_char_index = len(stripped_line) - len(stripped_line.lstrip(' '))
                print(f"[Line {line_number}] {stripped_line}")
                print(" " * (len(f"[Line {line_number}] ") + first_char_index) + "^")
                print(f"GuythonError: {e}")
        except Exception as e:
            if not importing:
                stripped_line = original_line.rstrip('\n')
                first_char_index = len(stripped_line) - len(stripped_line.lstrip(' '))
                print(f"[Line {line_number}] {stripped_line}")
                print(" " * (len(f"[Line {line_number}] ") + first_char_index) + "^")
                print(f"Unexpected error: {e}")

    def _process_command(self, code: str, indent: int, importing: bool):
        """Process a single command"""
        #print(f"DEBUG: _process_command called with code='{code}'")
        #print(f"DEBUG: code.endswith('_') = {code.endswith('_')}")
        #print(f"DEBUG: code ends with: '{code[-5:]}' (last 5 chars)")

        # Apply aliases
        for alias, replacement in self.aliases.items():
            if code.startswith(alias + " "):
                code = code.replace(alias, replacement, 1)

        # Handle eval command
        if code.startswith('eval '):
            #print("DEBUG: Handling eval command")
            self._handle_eval_command(code, importing)
            return

        if code.startswith('input"') and code.endswith('"'):
            #print("DEBUG: Handling input with double quotes")
            return self._handle_input(code, importing)
        elif code.startswith("input'") and code.endswith("'"):
            #print("DEBUG: Handling input with single quotes")
            return self._handle_input(code, importing)
        elif '=input"' in code and code.count('"') == 2:
            #print("DEBUG: Handling input assignment with double quotes")
            return self._handle_input_assignment(code, importing)
        elif "=input '" in code and code.count("'") == 2:
            #print("DEBUG: Handling input assignment with single quotes")
            return self._handle_input_assignment(code, importing)
        elif code.startswith("alias "):
            #print("DEBUG: Handling alias")
            self._handle_alias(code)
        elif code.startswith("else"):
            #print("DEBUG: Handling else")
            self._handle_else(indent)
        elif code.startswith("exit_"):
            #print("DEBUG: Handling exit")
            self.os._exit(0)
            self.sys.exit(0)
        elif code.startswith("gpd "):
            #print("DEBUG: Handling gpd command")
            self._handle_gpd_command(code[4:])
        elif code.startswith('def'):
            #print("DEBUG: Handling function definition")
            self._handle_function_definition(code, indent, importing)
        elif code.startswith('while'):
            #print("DEBUG: Handling while loop")
            self._handle_while(code, indent, importing)
        elif code.startswith('if'):
            #print("DEBUG: Handling if statement")
            self._handle_if(code, indent, importing)
        elif self.loop_stack and indent > self.loop_stack[-1][1]:
            #print("DEBUG: Adding to loop block")
            self.loop_stack[-1][2].append((indent, code))
        elif self.if_stack and not self.if_stack[-1][0] and indent > self.if_stack[-1][1]:
            #print("DEBUG: Skipping line due to false if condition")
            self._debug_print(f"Skipping line due to false if condition: {code}")
            return
        elif code.startswith('goto'):
            #print("DEBUG: Handling goto")
            self._handle_goto(code, importing)
            return
        elif code.startswith("guython"):
            #print("DEBUG: Handling guython command")
            self._handle_guython_command(code, importing)
            return
        # Check for function call pattern: word_ [args] or just word_
        elif ('_ ' in code or code.endswith('_')) and not any(code.startswith(cmd) for cmd in ['def', 'while', 'if', 'print', 'input', 'alias', 'else', 'exit', 'gpd', 'goto', 'guython', 'read', 'write', 'import']):
            #print(f"DEBUG: FOUND FUNCTION CALL! code='{code}'")
            self._handle_function_call(code, importing)
            return
        elif code.startswith('printinput') or code.startswith('print input'):
            #print("DEBUG: Handling print input")
            self._handle_print_input(importing)
        elif '=' in code and not code.startswith('print') and code != "5+5=4":
            #print("DEBUG: Handling assignment")
            self._handle_assignment(code, importing)
        elif code.startswith('print'):
            #print("DEBUG: Handling print statement")
            self._handle_print(code, importing)
        elif code == "5+5=4":
            #print("DEBUG: Handling 5+5=4 easter egg")
            if not importing:
                print("chatgpt actually said this bruh 😭")
        elif code == "9+10":
            #print("DEBUG: Handling 9+10 easter egg")
            if not importing:
                print("21")
                print("you stupid")
                print("its 19")
        elif code == "ver" and "=" not in code:
            #print("DEBUG: Handling version command")
            if not importing:
                print("Guython", VERSION)
        elif '[' in code and ']' in code and '=' not in code:
            #print("DEBUG: Handling array access")
            if not importing:
                try:
                    result = self._handle_array_access(code)
                    if result is not None:
                        print(result)
                        self.last_output = result
                except GuythonError:
                    raise
        else:
            #print("DEBUG: Falling back to expression evaluation")
            if not importing:
                try:
                    evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                    result = evaluator.evaluate(code)
                    if result is not None:
                        print(result)
                        self.last_output = result
                except GuythonError:
                    raise
                except Exception as e:
                    raise GuythonRuntimeError(f"Error evaluating expression: {e}")
    
    def _handle_gpd_command(self, command: str):
        """Handle GPD package commands"""
        parts = command.split(maxsplit=1)
        if not parts:
            raise GuythonSyntaxError("Invalid GPD command")

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        try:
            if cmd == "install":
                if not args:
                    raise GuythonSyntaxError("Missing package name")
                self.gpd.install(args.strip('"\''))
            elif cmd == "import":
                if not args:
                    raise GuythonSyntaxError("Missing package name")
                import_parts = args.split(maxsplit=2)
                if len(import_parts) == 1:
                    self.gpd.import_pkg(import_parts[0].strip('"\''))
                elif len(import_parts) == 3 and import_parts[1] == "as":
                    self.gpd.import_pkg(import_parts[0].strip('"\''), import_parts[2].strip('"\''))
                else:
                    raise GuythonSyntaxError("Invalid import syntax. Use: gpd import <package> [as <alias>]")
            elif cmd == "list":
                print("Installed packages:")
                for pkg in self.gpd.list_packages():
                    print(f"- {pkg} v{self.gpd.package_index[pkg]['version']}")
            elif cmd == "uninstall":
                if not args:
                    raise GuythonSyntaxError("Missing package name")
                self.gpd.uninstall(args.strip('"\''))
            elif cmd == "pkgs":
                try:
                    remote_index = self.gpd._fetch_remote_index()
                    print("Available packages fetched from repository:")
                    max_name_len = max(len(pkg) for pkg in remote_index.keys()) if remote_index else 0

                    for pkg, data in remote_index.items():
                        version = data.get('version', '?.?.?')
                        description = data.get('description', 'No description available')
                        # Format with consistent spacing
                        print(f"- {pkg.ljust(max_name_len)} (v{version}): {description}")
                except Exception as e:
                    print(f"Error fetching remote packages: {e}")
            elif cmd == "help":
                try:
                    print("Available GPD commands:")
                    print("""
pkgs             -  fetches all packages available for download
list             -  lists all install packages
install {name}   -  installs package with that name
uninstall {name} -  uninstalls the package with that name
import {name}    -  imports the package with that name
                    """)
                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
            else:
                raise GuythonSyntaxError(f"Unknown GPD command: '{cmd}', use 'gpd help' to list all GPD commands")
        except GuythonRuntimeError as e:
            print(f"GPD Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
    
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

    def _parse_gui_args(self, code: str) -> List[str]:
        """Parse GUI command arguments, respecting quoted strings"""
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = None
        i = 0

        while i < len(code):
            char = code[i]

            if not in_quotes:
                if char in ['"', "'"]:
                    in_quotes = True
                    quote_char = char
                    current_arg += char
                elif char == ' ':
                    if current_arg:
                        args.append(current_arg)
                        current_arg = ""
                else:
                    current_arg += char
            else:
                current_arg += char
                if char == quote_char:
                    in_quotes = False
                    quote_char = None

            i += 1

        if current_arg:
            args.append(current_arg)
    
        return args

    def _handle_gui_command(self, code: str, importing: bool):
        """Handle GUI-related commands"""
        if importing:
            return

        # Parse arguments properly
        args = self._parse_gui_args(code)
        if not args:
            return

        command = args[0]

        try:
            if command == "createWindow":
                # Syntax: createWindow "title" width height [resizable]
                title = "Guython Window"
                width, height = 400, 300
                resizable = True

                if len(args) >= 2:
                    title = args[1].strip('"\'')
                if len(args) >= 4:
                    width = int(args[2])
                    height = int(args[3])
                if len(args) >= 5:
                    resizable = args[4].lower() == "true"

                window_id = self.gui.create_window(title, width, height, resizable)
                print(f"Created window: {window_id}")

            elif command == "createButton":
                # Syntax: createButton "text" x y width height [command]
                text = "Button"
                x, y, width, height = 10, 10, 100, 30
                command_func = None

                if len(args) >= 2:
                    text = args[1].strip('"\'')
                if len(args) >= 6:
                    x = int(args[2])
                    y = int(args[3])
                    width = int(args[4])
                    height = int(args[5])
                if len(args) >= 7:
                    command_func = args[6]

                widget_id = self.gui.create_button(text, x, y, width, height, command_func, self)
                print(f"Created button: {widget_id}")

            elif command == "createLabel":
                # Syntax: createLabel "text" x y width height
                text = "Label"
                x, y, width, height = 10, 10, 100, 30

                if len(args) >= 2:
                    text = args[1].strip('"\'')
                if len(args) >= 6:
                    x = int(args[2])
                    y = int(args[3])
                    width = int(args[4])
                    height = int(args[5])

                widget_id = self.gui.create_label(text, x, y, width, height)
                print(f"Created label: {widget_id}")

            elif command == "createEntry":
                # Syntax: createEntry x y width height ["placeholder"]
                x, y, width, height = 10, 10, 100, 30
                placeholder = ""

                if len(args) >= 5:
                    x = int(args[1])
                    y = int(args[2])
                    width = int(args[3])
                    height = int(args[4])
                if len(args) >= 6:
                    placeholder = args[5].strip('"\'')

                widget_id = self.gui.create_entry(x, y, width, height, placeholder)
                print(f"Created entry: {widget_id}")

            elif command == "createImage":
                # Syntax: createImage "path" x y [width height]
                if len(args) < 4:
                    raise GuythonSyntaxError("createImage requires: path x y [width height]")

                path = args[1].strip('"\'')
                x = int(args[2])
                y = int(args[3])
                width = int(args[4]) if len(args) >= 5 else None
                height = int(args[5]) if len(args) >= 6 else None

                widget_id = self.gui.create_image(path, x, y, width, height)
                print(f"Created image: {widget_id}")

            elif command == "showMessage":
                # Syntax: showMessage "title" "message" [type]
                title = "Message"
                message = ""
                msg_type = "info"

                if len(args) >= 2:
                    title = args[1].strip('"\'')
                if len(args) >= 3:
                    message = args[2].strip('"\'')
                if len(args) >= 4:
                    msg_type = args[3]

                self.gui.show_message(title, message, msg_type)

            elif command == "setWindowColor":
                # Syntax: setWindowColor "#ffffff"
                color = "#ffffff"
                if len(args) >= 2:
                    color = args[1].strip('"\'')
                self.gui.set_window_color(color)

            elif command == "startGui":
                self.gui.start_gui()
                print("GUI started")

            elif command == "waitGui":
                self.gui.wait_gui()
                

            else:
                raise GuythonSyntaxError(f"Unknown GUI command: {command}")

        except ValueError as e:
            raise GuythonSyntaxError(f"Invalid parameters for {command}: {e}")
        except Exception as e:
            raise GuythonRuntimeError(f"GUI error in {command}: {e}")

    def _handle_set_text(self, code: str, importing: bool):
        """Handle setText command to set text of GUI widgets"""
        if importing:
            return

        # Parse the command properly
        parts = code.split(maxsplit=2)
        if len(parts) < 3:
            raise GuythonSyntaxError("setText syntax: setText <widgetId> <text>")

        _, widget_id, text_source = parts

        # Debug output to verify widget ID
        self._debug_print(f"Attempting to set text on widget: {widget_id}")
        self._debug_print(f"Available widgets: {list(self.gui.widgets.keys())}")

        # Evaluate the text source
        try:
            if (text_source.startswith('"') and text_source.endswith('"')) or \
               (text_source.startswith("'") and text_source.endswith("'")):
                text_value = text_source[1:-1]
            else:
                evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                text_value = str(evaluator.evaluate(text_source))
        except Exception as e:
            raise GuythonRuntimeError(f"Error evaluating text: {e}")

        # Set the widget text
        try:
            # Access the GUI manager's widgets directly
            if widget_id in self.gui.widgets:
                self.gui.set_widget_text(widget_id, text_value)
                self._debug_print(f"Successfully set text of {widget_id} to: {text_value}")
            else:
                raise GuythonRuntimeError(f"Widget not found: {widget_id}. Available widgets: {list(self.gui.widgets.keys())}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error setting widget text: {e}")

    def _handle_read_text(self, code: str, importing: bool):
        """Handle readText command to get text from GUI widgets"""
        if importing:
            return

        # Parse: readText widgetId variableName
        parts = self._parse_gui_args(code)
        if len(parts) != 3:
            raise GuythonSyntaxError("readText syntax: readText <widgetId> <variableName>")

        _, widget_id, var_name = parts

        # Validate variable name
        if not self._validate_variable_name(var_name):
            raise GuythonSyntaxError(f"Invalid variable name: '{var_name}'")

        # Get text from widget
        try:
            text_value = self.gui.get_widget_value(widget_id)

            # Try to convert to number if possible
            try:
                if text_value.replace('.', '', 1).isdigit():
                    self.variables[var_name] = float(text_value)
                elif text_value.lstrip('-').isdigit():
                    self.variables[var_name] = int(text_value)
                else:
                    # Keep as string if not a number
                    self.variables[var_name] = text_value
            except (ValueError, AttributeError):
                # Keep as string if conversion fails or if text_value is None
                self.variables[var_name] = text_value if text_value is not None else ""

            self._debug_print(f"Read text from {widget_id} into {var_name}: {self.variables[var_name]}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error reading from widget {widget_id}: {e}")
    
    def _handle_function_definition(self, code: str, indent: int, importing: bool):
        """Store function name, args, and prepare to capture function body"""
        #print(f"DEBUG: Handling function definition: {code}")

        # Must start with 'def' and have an underscore separating name and args
        if not code.startswith('def') or '_' not in code:
            raise GuythonSyntaxError("Function must be defined as 'def<name>_ [args]'")

        # Extract everything after 'def'
        after_def = code[3:].strip()  # e.g. 'foo_ x, y'
        #print(f"DEBUG: after_def = '{after_def}'")

        # Split name and args by first underscore '_'
        if '_' not in after_def:
            raise GuythonSyntaxError("Function definition missing trailing underscore")

        func_name, *rest = after_def.split('_', 1)
        func_name = func_name.strip()
        args_str = rest[0].strip() if rest else ""
        #print(f"DEBUG: func_name = '{func_name}', args_str = '{args_str}'")

        # Parse args (comma separated)
        args = [arg.strip() for arg in args_str.split(',')] if args_str else []
        #print(f"DEBUG: parsed args = {args}")

        # Validate function name
        if not self._validate_variable_name(func_name):
            raise GuythonSyntaxError(f"Invalid function name: '{func_name}'")

        # Validate argument names
        for arg in args:
            if arg and not self._validate_variable_name(arg):
                raise GuythonSyntaxError(f"Invalid argument name: '{arg}'")

        # Store function as dict with args and empty body list
        self.functions[func_name] = {
            'args': args,
            'body': []
        }

        self.defining_function = (func_name, indent)
        self.function_stack = []  # Reset function stack
        #if not importing:
            #print(f"DEFINED: {func_name} with args {args}")

    def _handle_alias(self, code: str):
        # Example: alias p = print
        try:
            _, rest = code.split("alias", 1)
            alias_def = rest.strip()
            name, target = alias_def.split("=", 1)
            name = name.strip()
            target = target.strip()

            if not self._validate_variable_name(name):
                raise GuythonSyntaxError(f"Invalid alias name: {name}")
            if not target:
                raise GuythonSyntaxError("Alias target cannot be empty")

            self.aliases[name] = target
            self._debug_print(f"Alias created: {name} -> {target}")
        except ValueError:
            raise GuythonSyntaxError("Invalid alias syntax. Use: alias name = target")


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
            self.else_stack.append((not is_true, indent))
            self._debug_print(f"If condition '{condition}' evaluated to: {is_true}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error in if condition: {e}")
    def _handle_else(self, indent: int):
        if not self.else_stack:
            raise GuythonSyntaxError("Unexpected 'else' without matching 'if'")

        should_run, if_indent = self.else_stack[-1]

        if indent <= if_indent:
            raise GuythonSyntaxError("Else block must be indented under its matching if")

        self.if_stack.append((should_run, indent))  # treat like a conditional block

    
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

    def _handle_guython_command(self, code: str, importing: bool):
        """Handle guython command to execute another Guython file"""
        if importing:
            return

        filename = code[8:].strip()  # Remove "guython " prefix

        if not (filename.endswith('.gy') or filename.endswith('.guy')):
            raise GuythonSyntaxError("Invalid file type. Given file must be .gy or .guy")

        if not os.path.isfile(filename):
            raise GuythonRuntimeError(f"File not found: {filename}")

        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
                self.run_program(lines)
        except Exception as e:
            raise GuythonRuntimeError(f"Error executing file {filename}: {e}")
    
    def _handle_function_call(self, code: str, importing: bool):
        """Handle calls like 'funcname_ arg1, arg2'"""
        #print(f"DEBUG: Handling function call: '{code}'")

        # Split code into function name and arg string
        if ' ' in code:
            func_name, args_str = code.split(' ', 1)
            args_str = args_str.strip()
            # Split arguments by comma, but be careful with whitespace
            if args_str:
                passed_args = [arg.strip() for arg in args_str.split(',')]
            else:
                passed_args = []
        else:
            func_name = code.strip()
            passed_args = []

        #print(f"DEBUG: func_name='{func_name}', passed_args={passed_args}")

        # Remove trailing underscore from func_name
        if not func_name.endswith('_'):
            raise GuythonRuntimeError(f"Function call must end with '_', got: {func_name}")
        func_name = func_name[:-1]

        #print(f"DEBUG: Looking for function '{func_name}' in functions: {list(self.functions.keys())}")

        # Check function exists
        if func_name not in self.functions:
            available = list(self.functions.keys())
            raise GuythonRuntimeError(f"Function '{func_name}' not found. Available: {available}")

        func = self.functions[func_name]
        declared_args = func['args']
        body = func['body']

        #print(f"DEBUG: Function found - declared_args={declared_args}, body={body}")

        # Check argument count
        if len(passed_args) != len(declared_args):
            raise GuythonRuntimeError(f"Function '{func_name}' expects {len(declared_args)} args, got {len(passed_args)}")

        # Save current variable state
        saved_vars = self.variables.copy()

        try:
            # Evaluate passed arguments and bind to parameter names
            for i, (param_name, arg_expr) in enumerate(zip(declared_args, passed_args)):
                #print(f"DEBUG: Processing argument {i}: param_name='{param_name}', arg_expr='{arg_expr}'")
                try:
                    # Simple argument evaluation
                    arg_value = self._evaluate_argument(arg_expr)
                    #print(f"DEBUG: Evaluated '{arg_expr}' to {arg_value}")

                    # Bind to parameter name in current scope
                    self.variables[param_name] = arg_value
                    #print(f"DEBUG: Bound parameter {param_name} = {arg_value}")
                except Exception as e:
                    print(f"DEBUG: Error evaluating argument: {e}")
                    raise GuythonRuntimeError(f"Error evaluating argument {i+1} ({arg_expr}): {e}")

            #print(f"DEBUG: About to execute function body with {len(body)} lines")
            # Execute function body
            for indent, line in body:
                #print(f"DEBUG: Executing function body line: indent={indent}, line='{line}'")
                # Reconstruct the line with proper indentation
                full_line = '.' * indent + line
                #print(f"DEBUG: Reconstructed line: '{full_line}'")
                self.run_line(full_line, importing=importing, line_number=self.current_line_number)

            #print(f"DEBUG: Function '{func_name}' execution complete")

        finally:
            # Restore original variable state (simple local scope simulation)
            # Keep any global variables that were modified, but remove parameters
            for param_name in declared_args:
                if param_name in saved_vars:
                    self.variables[param_name] = saved_vars[param_name]
                elif param_name in self.variables:
                    del self.variables[param_name]

    def _evaluate_argument(self, arg_expr: str):
        """Simple argument evaluation that handles common cases"""
        arg_expr = arg_expr.strip()
        #print(f"DEBUG: _evaluate_argument called with '{arg_expr}'")

        # String literals
        if (arg_expr.startswith('"') and arg_expr.endswith('"')) or \
           (arg_expr.startswith("'") and arg_expr.endswith("'")):
            result = arg_expr[1:-1]
            #print(f"DEBUG: String literal result: '{result}'")
            return result

        # Number literals
        try:
            if '.' in arg_expr:
                result = float(arg_expr)
                #print(f"DEBUG: Float literal result: {result}")
                return result
            else:
                result = int(arg_expr)
                #print(f"DEBUG: Int literal result: {result}")
                return result
        except ValueError:
            pass
        
        # Variable lookup
        if arg_expr in self.variables:
            result = self.variables[arg_expr]
            #print(f"DEBUG: Variable lookup result: '{arg_expr}' = {result}")
            return result

        # Array literals
        if arg_expr.startswith('[') and arg_expr.endswith(']'):
            try:
                result = self._parse_array_literal(arg_expr)
                print(f"DEBUG: Array literal result: {result}")
                return result
            except:
                pass
            
        #print(f"DEBUG: Falling back to expression evaluator for '{arg_expr}'")
        # Fall back to expression evaluator for complex expressions
        try:
            evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
            result = evaluator.evaluate(arg_expr)
            #print(f"DEBUG: Expression evaluator result: {result}")
            return result
        except Exception as e:
            #print(f"DEBUG: Expression evaluator failed: {e}")
            raise GuythonRuntimeError(f"Cannot evaluate argument '{arg_expr}': {e}")

    
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
        """Handle input assignment with prompts"""
        if importing:
            return

        # Handle both single and double quoted prompts
        if '=input"' in code:
            parts = code.split('=input"', 1)
            var_name = parts[0].strip()
            prompt = parts[1][:-1]  # Remove trailing quote
        elif "=input '" in code:
            parts = code.split("=input '", 1)
            var_name = parts[0].strip()
            prompt = parts[1][:-1]  # Remove trailing quote
        else:
            raise GuythonSyntaxError("Invalid input assignment syntax")

        if not self._validate_variable_name(var_name):
            raise GuythonSyntaxError(f"Invalid variable name: '{var_name}'")

        try:
            user_input = input(prompt)

            # Try to convert to number if possible
            try:
                if '.' in user_input and user_input.replace('.', '', 1).isdigit():
                    self.variables[var_name] = float(user_input)
                elif user_input.lstrip('-').isdigit():
                    self.variables[var_name] = int(user_input)
                else:
                    self.variables[var_name] = user_input
            except ValueError:
                self.variables[var_name] = user_input

            self._debug_print(f"Assigned to {var_name}: {self.variables[var_name]}")
        except EOFError:
            self.variables[var_name] = ""
        except KeyboardInterrupt:
            raise

    def _handle_input(self, code: str, importing: bool):
        """Handle standalone input with prompt"""
        if importing:
            return

        if code.startswith('input"') and code.endswith('"'):
            prompt = code[6:-1]
        elif code.startswith("input'") and code.endswith("'"):
            prompt = code[6:-1]
        else:
            prompt = ""

        try:
            user_input = input(prompt) if prompt else input()
            print(user_input)  # Echo input like Python
            return user_input
        except EOFError:
            print()  # Handle EOF
            return ""
        except KeyboardInterrupt:
            raise

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in appropriate units"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _get_user_confirmation(self, message: str) -> bool:
        """Get Y/N confirmation from user"""
        try:
            response = input(f"{message} (Y/N): ").strip().lower()
            return response in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            return False


    def _handle_read(self, code: str, importing: bool):
        """Handle read command with modifiers"""
        # Check for flags
        ignore_comments = '-ign' in code
        show_lines = '-lines' in code
        show_size = '-size' in code
        check_exists = '-exists' in code

        # Remove flags from code
        for flag in ['-ign', '-lines', '-size', '-exists']:
            code = code.replace(flag, '')
        code = code.strip()

        parts = code.split(None, 2)
        if len(parts) != 3:
            raise GuythonSyntaxError("Read syntax: read [-ign] [-lines] [-size] [-exists] {filePath} {fileName}.{fileExtension}")

        _, file_path, filename = parts
        full_path = os.path.join(file_path, filename) if file_path != '.' else filename

        # Handle -exists flag
        if check_exists:
            exists = os.path.isfile(full_path)
            if not importing:
                print("true" if exists else "false")
            return

        # Handle -size flag
        if show_size:
            try:
                size = os.path.getsize(full_path)
                if not importing:
                    print(self._format_file_size(size))
                return
            except FileNotFoundError:
                raise GuythonRuntimeError(f"File not found: {full_path}")
            except Exception as e:
                raise GuythonRuntimeError(f"Error getting file size {full_path}: {e}")

        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if show_lines:
                    lines = f.readlines()
                    # Remove newlines and apply comment stripping if needed
                    if ignore_comments:
                        lines = [self._strip_comments(line.rstrip('\n')) for line in lines]
                    else:
                        lines = [line.rstrip('\n') for line in lines]

                    if not importing:
                        for i, line in enumerate(lines, 1):
                            print(f"{i}: {line}")
                else:
                    content = f.read()
                    if ignore_comments:
                        content = self._strip_comments(content)
                    if not importing:
                        print(content)

            self._debug_print(f"Read file: {full_path}")
        except FileNotFoundError:
            raise GuythonRuntimeError(f"File not found: {full_path}")
        except PermissionError:
            raise GuythonRuntimeError(f"Permission denied reading file: {full_path}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error reading file {full_path}: {e}")

    def _handle_write(self, code: str, importing: bool):
        """Handle write command with modifiers"""
        # Check for flags
        add_mode = '-add' in code
        ignore_comments = '-ign' in code
        create_only = '-create' in code

        # Handle permissions flag
        permissions = None
        if '-permissions' in code:
            # Extract permissions value
            perm_match = re.search(r'-permissions\s+(\d+)', code)
            if perm_match:
                permissions = perm_match.group(1)
                code = re.sub(r'-permissions\s+\d+', '', code)
            else:
                raise GuythonSyntaxError("Permissions syntax: -permissions <mode> (e.g., -permissions 755)")

        # Remove other flags
        for flag in ['-add', '-ign', '-create']:
            code = code.replace(flag, '')
        code = code.strip()

        parts = code.split(None, 3)
        if len(parts) != 4:
            syntax_msg = "Write syntax: write [-add] [-ign] [-create] [-permissions <mode>] {filePath} {fileName}.{fileExtension} {fileContents}"
            raise GuythonSyntaxError(syntax_msg)

        _, file_path, filename, content = parts
        full_path = os.path.join(file_path, filename) if file_path != '.' else filename

        # Check if file exists and handle -create flag
        file_exists = os.path.isfile(full_path)
        if create_only and file_exists:
            if not importing:
                print(f"File already exists: {full_path}")
            return

        # Get confirmation if file exists and has content (and not in add mode)
        if file_exists and not add_mode and not importing:
            try:
                # Check if file has content
                with open(full_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read().strip()

                if existing_content:  # File has content
                    if not self._get_user_confirmation(f"File '{full_path}' already contains data. Overwrite?"):
                        print("Write operation cancelled.")
                        return
            except Exception:
                pass  # If we can't read the file, proceed with write attempt
            
        # Process content
        if (content.startswith('"') and content.endswith('"')) or \
           (content.startswith("'") and content.endswith("'")):
            content = content[1:-1]
        else:
            try:
                evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                content = str(evaluator.evaluate(content))
            except:
                pass
            
        if ignore_comments:
            content = self._strip_comments(content)

        try:
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(full_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            # Write file
            mode = 'a' if add_mode else 'w'
            with open(full_path, mode, encoding='utf-8') as f:
                if add_mode:
                    f.write('\n' + content)
                else:
                    f.write(content)

            # Set permissions if specified
            if permissions:
                try:
                    os.chmod(full_path, int(permissions, 8))  # Convert octal string to int
                except ValueError:
                    raise GuythonRuntimeError(f"Invalid permissions format: {permissions}")
                except Exception as e:
                    raise GuythonRuntimeError(f"Error setting permissions: {e}")

            action = "appended to" if add_mode else "written"
            if not importing:
                print(f"File {action}: {full_path}")
            self._debug_print(f"{'Appended to' if add_mode else 'Wrote'} file: {full_path}")

        except PermissionError:
            raise GuythonRuntimeError(f"Permission denied writing to file: {full_path}")
        except Exception as e:
            raise GuythonRuntimeError(f"Error writing file {full_path}: {e}")
    
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