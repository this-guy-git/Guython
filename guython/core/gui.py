import tkinter as tk
from tkinter import messagebox, filedialog, colorchooser
import threading
import time
from PIL import Image, ImageTk

from .errors import GuythonRuntimeError


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
