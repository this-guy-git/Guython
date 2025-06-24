# Guython Package Manager
from packages import GPD

import re
import math
import os
import sys
import ast
import operator
import tkinter as tk
import threading
import time
from tkinter import ttk, messagebox, filedialog, colorchooser
from PIL import Image, ImageTk
from types import SimpleNamespace
from typing import Dict, List, Tuple, Any, Optional, Union

# Version constant
VERSION = "v1.2.0b25620"

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


class GuythonGUI:
    """GUI manager for Guython"""
    
    def __init__(self, interpreter=None):
        self.windows = {}
        self.widgets = {}
        self.current_window = None
        self.widget_counter = 0
        self.running = False
        self.interpreter = interpreter
        
    def create_window(self, title="Guython Window", width=400, height=300, resizable=True):
        """Create a new window"""
        window = tk.Tk() if not self.windows else tk.Toplevel()
        window.title(title)
        window.geometry(f"{width}x{height}")
        window.resizable(resizable, resizable)
        
        window_id = f"window_{len(self.windows)}"
        self.windows[window_id] = window
        self.current_window = window_id
        
        # Handle window closing - FIXED VERSION
        def on_closing():
            try:
                # Remove the window from our tracking
                if window_id in self.windows:
                    del self.windows[window_id]
                
                # Clean up any widgets associated with this window
                widgets_to_remove = []
                for widget_id, widget in self.widgets.items():
                    try:
                        # Check if widget belongs to this window
                        if widget.winfo_toplevel() == window:
                            widgets_to_remove.append(widget_id)
                    except tk.TclError:
                        # Widget is already destroyed
                        widgets_to_remove.append(widget_id)
                
                # Remove the widgets from our tracking
                for widget_id in widgets_to_remove:
                    del self.widgets[widget_id]
                
                # Update current window if this was the current one
                if self.current_window == window_id:
                    if self.windows:
                        # Set current window to any remaining window
                        self.current_window = list(self.windows.keys())[0]
                    else:
                        self.current_window = None
                
                # If no windows left, stop the GUI
                if len(self.windows) == 0:
                    self.running = False
                
                # Destroy the window
                window.destroy()
                
            except Exception as e:
                print(f"Error during window close: {e}")
                # Force cleanup even if there's an error
                self.running = False
                try:
                    window.destroy()
                except:
                    pass
        
        window.protocol("WM_DELETE_WINDOW", on_closing)
        return window_id
    
    def create_button(self, text="Button", x=10, y=10, width=100, height=30, command=None, interpreter=None):
        if not self.current_window or self.current_window not in self.windows:
            raise GuythonRuntimeError("No window available. Create a window first.")

        window = self.windows[self.current_window]
        button = tk.Button(window, text=text, width=width//8, height=height//20)
        button.place(x=x, y=y, width=width, height=height)

        if command and interpreter:
            def callback():
                try:
                    print(f"BUTTON PRESS: {command}")  # Debug
                    # Create temporary code to execute
                    temp_code = f"{command}"
                    interpreter.run_line(temp_code)
                except Exception as e:
                    print(f"BUTTON ERROR: {e}")
            
            button.config(command=callback)

        widget_id = f"button_{self.widget_counter}"
        self.widgets[widget_id] = button
        self.widget_counter += 1
        return widget_id
    
    def create_label(self, text="Label", x=10, y=10, width=100, height=30):
        """Create a label widget"""
        if not self.current_window or self.current_window not in self.windows:
            raise GuythonRuntimeError("No window available. Create a window first.")
        
        window = self.windows[self.current_window]
        label = tk.Label(window, text=text)
        label.place(x=x, y=y, width=width, height=height)
        
        widget_id = f"label_{self.widget_counter}"
        self.widgets[widget_id] = label
        self.widget_counter += 1
        return widget_id
    
    def create_entry(self, x=10, y=10, width=100, height=30, placeholder=""):
        """Create a text entry widget with proper placeholder handling"""
        if not self.current_window or self.current_window not in self.windows:
            raise GuythonRuntimeError("No window available. Create a window first.")

        window = self.windows[self.current_window]
        entry = tk.Entry(window)
        entry.place(x=x, y=y, width=width, height=height)

        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg='grey')
            entry.placeholder = placeholder  # Store placeholder text

            def on_focus_in(event):
                if entry.get() == entry.placeholder:
                    entry.delete(0, tk.END)
                    entry.config(fg='black')

            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, entry.placeholder)
                    entry.config(fg='grey')

            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)

        widget_id = f"entry_{self.widget_counter}"
        self.widgets[widget_id] = entry
        self.widget_counter += 1
        return widget_id
    
    def create_image(self, image_path, x=10, y=10, width=None, height=None):
        """Create an image widget"""
        if not self.current_window or self.current_window not in self.windows:
            raise GuythonRuntimeError("No window available. Create a window first.")
        
        try:
            # Load and resize image
            pil_image = Image.open(image_path)
            if width and height:
                pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(pil_image)
            
            window = self.windows[self.current_window]
            label = tk.Label(window, image=photo)
            label.image = photo  # Keep a reference
            label.place(x=x, y=y)
            
            widget_id = f"image_{self.widget_counter}"
            self.widgets[widget_id] = label
            self.widget_counter += 1
            return widget_id
            
        except Exception as e:
            raise GuythonRuntimeError(f"Error loading image '{image_path}': {e}")
    
    def set_widget_text(self, widget_id: str, text: str):
        """Set text of a widget with improved lookup"""
        # First try exact match
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
        else:
            # Fallback to search by suffix (e.g., "label" matches "label_2")
            matching = [k for k in self.widgets.keys() if k.endswith(widget_id)]
            if not matching:
                raise ValueError(f"Widget ID not found: {widget_id}")
            widget = self.widgets[matching[0]]

        text = str(text)  # Ensure we have a string

        try:
            if isinstance(widget, (tk.Label, tk.Button)):
                widget.config(text=text)
            elif isinstance(widget, tk.Entry):
                widget.delete(0, tk.END)
                widget.insert(0, text)
                if hasattr(widget, 'placeholder') and widget.placeholder == text:
                    widget.config(fg='grey')
                else:
                    widget.config(fg='black')
            else:
                # Generic fallback
                if hasattr(widget, 'config') and 'text' in widget.config():
                    widget.config(text=text)
                elif hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                    widget.delete(0, tk.END)
                    widget.insert(0, text)
                else:
                    raise ValueError(f"Cannot set text on widget type: {type(widget)}")
        except tk.TclError as e:
            raise ValueError(f"Error setting widget text: {e}")
    
    def get_widget_text(self, widget_id):
        """Get text from a widget"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            if hasattr(widget, 'get'):
                return widget.get()
            elif hasattr(widget, 'cget'):
                return widget.cget('text')
        return ""
    
    def get_widget_value(self, widget_id: str) -> str:
        """Get value from a widget (enhanced version)"""
        if widget_id in self.widgets:
            widget = self.widgets[widget_id]
            try:
                if isinstance(widget, tk.Entry):
                    # Entry widgets
                    value = widget.get()
                    # Don't return placeholder text
                    if widget.cget('fg') == 'grey':
                        return ""
                    return value
                elif isinstance(widget, tk.Label):
                    # Label widgets
                    return widget.cget('text')
                elif isinstance(widget, tk.Button):
                    # Button widgets
                    return widget.cget('text')
                else:
                    # Default case for other widgets
                    if hasattr(widget, 'get'):
                        return widget.get()
                    elif hasattr(widget, 'cget'):
                        return widget.cget('text')
                    return ""
            except tk.TclError:
                return ""
        return ""

    def focus_widget(self, widget_id):
        """Set focus to a specific widget"""
        if widget_id in self.widgets:
            try:
                self.widgets[widget_id].focus_set()
            except tk.TclError:
                pass

    def show_message(self, title="Message", message="", msg_type="info"):
        """Show a message box"""
        if msg_type == "error":
            messagebox.showerror(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)
    
    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor()
        return color[1] if color[1] else "#000000"
    
    def choose_file(self, file_types="*.*"):
        """Open file chooser dialog"""
        return filedialog.askopenfilename(filetypes=[("All files", file_types)])
    
    def set_window_color(self, color="#ffffff"):
        """Set background color of current window"""
        if self.current_window and self.current_window in self.windows:
            self.windows[self.current_window].config(bg=color)
    
    def start_gui(self):
        """Start the GUI event loop"""
        if self.windows:
            self.running = True
            # Run in a separate thread to not block the interpreter
            def run_mainloop():
                while self.running and self.windows:
                    try:
                        for window in list(self.windows.values()):
                            window.update()
                        time.sleep(0.01)  # Small delay to prevent high CPU usage
                    except:
                        break
            
            gui_thread = threading.Thread(target=run_mainloop, daemon=True)
            gui_thread.start()
    
    def wait_gui(self):
        """Wait for GUI to close (blocking)"""
        if self.windows:
            list(self.windows.values())[0].mainloop()
    
    def _execute_callback(self, command):
        """Execute a callback command (placeholder for now)"""
        print(f"Button clicked: {command}")

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
        self.program_lines: List[str] = []
        self.goto_max_jumps = 1000  # Prevent infinite goto loops
        self.goto_jump_count = 0
        self.gui = GuythonGUI(interpreter=self)
        self.gpd = GPD(self)
        self.functions = {}
        
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

        if code.startswith('input"') and code.endswith('"'):
            return self._handle_input(code, importing)
        elif code.startswith("input'") and code.endswith("'"):
            return self._handle_input(code, importing)
        elif '=input"' in code and code.count('"') == 2:
            return self._handle_input_assignment(code, importing)
        elif "=input '" in code and code.count("'") == 2:
            return self._handle_input_assignment(code, importing)

        elif code.startswith("gpd "):
            self._handle_gpd_command(code[4:])

        elif '.' in code and '(' in code and ')' in code:
            # Handle module.function(arg) calls
            try:
                module_path, rest = code.split('.', 1)
                func_call = rest.split('(', 1)
                func_name = func_call[0]
                args_str = func_call[1].rstrip(')')
                
                if module_path in self.variables:
                    module = self.variables[module_path]
                    if hasattr(module, func_name):
                        func = getattr(module, func_name)
                        if callable(func):
                            # Evaluate arguments
                            evaluator = ExpressionEvaluator(self.variables, SAFE_FUNCTIONS)
                            args = []
                            kwargs = {}
                            if args_str:
                                for arg in args_str.split(','):
                                    if '=' in arg:
                                        key, value = arg.split('=', 1)
                                        kwargs[key.strip()] = evaluator.evaluate(value.strip())
                                    else:
                                        args.append(evaluator.evaluate(arg.strip()))
                            
                            result = func(*args, **kwargs)
                            if result is not None and not importing:
                                print(result)
            except Exception as e:
                raise GuythonRuntimeError(f"Error in function call: {e}")

        # Function definition
        elif code.startswith('def'):
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

        # Guython command to execute another file
        elif code.startswith("guython"):
            self._handle_guython_command(code, importing)
            return

        # GUI commands
        elif code.split()[0] in ['createWindow', 'createButton', 'createLabel', 'createEntry', 
                                 'createImage', 'showMessage', 'setWindowColor', 'startGui', 'waitGui']:
            self._handle_gui_command(code, importing)

        # Read text from GUI widget
        elif code.startswith('readText'):
            self._handle_read_text(code, importing)

        # Set text of GUI widget
        elif code.startswith('setText'):
            self._handle_set_text(code, importing)

        # File operations
        elif code.startswith('read'):
            self._handle_read(code, importing)

        elif code.startswith('write'):
            self._handle_write(code, importing)

        # Import
        elif code.startswith("import"):
            self._handle_import(code, importing)

        # Function call
        elif code.endswith('_'):
            self._handle_function_call(code, importing)

        # Input operations - FIXED: Check these before general assignment
        elif code.startswith('printinput') or code.startswith('print input'):
            self._handle_print_input(importing)

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
        """Store functions exactly as defined"""
        if not code.startswith('def') or not code.endswith('_'):
            raise GuythonSyntaxError("Function must be defined as 'def<name>_'")

        func_name = code[3:]  # Get name after 'def'
        self.functions[func_name] = []  # Store with exact name
        self.defining_function = (func_name, indent)
        print(f"DEFINED: {func_name}")  # Debug
    
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
        """Handle function calls with exact matching"""
        print(f"CALLING: {code}")  # Debug

        if code not in self.functions:
            available = list(self.functions.keys())
            raise GuythonRuntimeError(
                f"Function '{code}' not found. Available: {available}"
            )

        # Execute function body
        for indent, line in self.functions[code]:
            self.run_line('.' * indent + line, importing)
    
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
