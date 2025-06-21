import sys
import base64
import random
import string
import platform
import math
import os
import zipfile
import hashlib
import webbrowser
from time import sleep
from datetime import datetime

class GuysMultitool:
    def __init__(self):
        # Initialize tools after all methods are defined
        self.fonts = [
            "block", "banner", "standard", "doom", "digital",
            "lean", "script", "starwars", "bulbhead", "univers"
        ]
        
    def initialize_tools(self):
        """Initialize tools dictionary after all methods are defined"""
        self.tools = {
            "1": {"name": "ASCII Art Generator", "func": self.ascii_art},
            "2": {"name": "Password Generator", "func": self.password_gen},
            "3": {"name": "File Encoder/Decoder", "func": self.file_ops},
            "4": {"name": "Unit Converter", "func": self.unit_convert},
            "5": {"name": "System Info", "func": self.system_info},
            "6": {"name": "Guython Interpreter", "func": self.guython_interpreter},
            "7": {"name": "QR Code Generator", "func": self.qr_code},
            "8": {"name": "Checksum Calculator", "func": self.checksum},
            "9": {"name": "Text to Speech", "func": self.text_to_speech},
            "10": {"name": "Directory Lister", "func": self.directory_lister},
            "11": {"name": "Web Search", "func": self.web_search},
            "12": {"name": "Zip Tool", "func": self.zip_tool},
            "0": {"name": "Exit", "func": self.exit_tool}
        }

    def clear_screen(self):
        """Clear terminal screen"""
        print("\n" * 50)

    def show_splash(self):
        """Show splash screen"""
        self.clear_screen()
        print("=" * 84)
        print(r"""
        
 ________  ___  ___      ___    ___ ________           _____ ______   _________   
|\   ____\|\  \|\  \    |\  \  /  /|\   ____\         |\   _ \  _   \|\___   ___\ 
\ \  \___|\ \  \\\  \   \ \  \/  / | \  \___|_        \ \  \\\__\ \  \|___ \  \_| 
 \ \  \  __\ \  \\\  \   \ \    / / \ \_____  \        \ \  \\|__| \  \   \ \  \  
  \ \  \|\  \ \  \\\  \   \/  /  /   \|____|\  \        \ \  \    \ \  \   \ \  \ 
   \ \_______\ \_______\__/  / /       ____\_\  \        \ \__\    \ \__\   \ \__\
    \|_______|\|_______|\___/ /       |\_________\        \|__|     \|__|    \|__|
                       \|___|/        \|_________|                                
                                                                                  
                                                                                  

        """.center(84))
        print("=" * 84)
        print("Now with 12 powerful tools!".center(84))
        print("=" * 84)
        sleep(3)

    def show_menu(self):
        """Display interactive menu"""
        self.clear_screen()
        print("\n" + "=" * 84)
        print(r"""
        
 ________  ___  ___      ___    ___ ________           _____ ______   _________   
|\   ____\|\  \|\  \    |\  \  /  /|\   ____\         |\   _ \  _   \|\___   ___\ 
\ \  \___|\ \  \\\  \   \ \  \/  / | \  \___|_        \ \  \\\__\ \  \|___ \  \_| 
 \ \  \  __\ \  \\\  \   \ \    / / \ \_____  \        \ \  \\|__| \  \   \ \  \  
  \ \  \|\  \ \  \\\  \   \/  /  /   \|____|\  \        \ \  \    \ \  \   \ \  \ 
   \ \_______\ \_______\__/  / /       ____\_\  \        \ \__\    \ \__\   \ \__\
    \|_______|\|_______|\___/ /       |\_________\        \|__|     \|__|    \|__|
                       \|___|/        \|_________|                                
                                                                                  
                                                                                  

        """.center(84))
        print("=" * 84)
        for key, tool in self.tools.items():
            print(f"[{key}] {tool['name']}")
        print("=" * 84)

    def run(self):
        """Main program loop"""
        self.initialize_tools()  # Initialize tools here
        self.show_splash()
        while True:
            self.show_menu()
            choice = input("\nSelect tool >> ").strip()
            
            if choice in self.tools:
                self.clear_screen()
                self.tools[choice]["func"]()
                if choice != "0":
                    input("\nPress Enter to continue...")
            else:
                print("! Invalid choice. Try again.")
                sleep(1)

    # --- Tool Implementations ---
    def ascii_art(self):
        """ASCII Art Generator"""
        print("\n" + "=" * 30)
        print("ASCII ART GENERATOR".center(30))
        print("=" * 30)
        
        text = input("Enter text: ").strip()
        if not text:
            print("! Error: Text cannot be empty")
            return

        print("\nAvailable fonts:")
        for i, font in enumerate(self.fonts, 1):
            print(f"{i}. {font}")
        
        try:
            font_choice = int(input("Select font (1-10): ")) - 1
            selected_font = self.fonts[font_choice]
        except (ValueError, IndexError):
            selected_font = "standard"
            print("! Defaulting to 'standard' font")

        try:
            import pyfiglet
            art = pyfiglet.figlet_format(text, font=selected_font)
            print("\n" + "=" * 60)
            print(f"Font: {selected_font}".center(60))
            print("=" * 60)
            print(art)
            print("=" * 60)
            
            if input("\nSave to file? (y/n): ").lower() == "y":
                with open("ascii_art.txt", "w") as f:
                    f.write(art)
                print("Saved to 'ascii_art.txt'")
        except ImportError:
            print("! Install pyfiglet first: pip install pyfiglet")

    def password_gen(self):
        """Password Generator"""
        print("\n" + "=" * 30)
        print("PASSWORD GENERATOR".center(30))
        print("=" * 30)
        
        try:
            length = int(input("Length (8-64): ").strip())
            length = max(8, min(64, length))
            use_upper = input("Uppercase letters? (y/n): ").lower() == "y"
            use_digits = input("Numbers? (y/n): ").lower() == "y"
            use_special = input("Special chars? (y/n): ").lower() == "y"
            
            chars = string.ascii_lowercase
            if use_upper: chars += string.ascii_uppercase
            if use_digits: chars += string.digits
            if use_special: chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
            
            password = ''.join(random.SystemRandom().choice(chars) for _ in range(length))
            print("\nGenerated Password:")
            print("-" * 30)
            print(password)
            print("-" * 30)
        except ValueError:
            print("! Invalid length")

    def file_ops(self):
        """File Encoder/Decoder"""
        print("\n" + "=" * 30)
        print("FILE ENCODER/DECODER".center(30))
        print("=" * 30)
        
        print("Operations:\n1. Base64 Encode\n2. Base64 Decode\n3. Hex Dump")
        try:
            op = int(input("Select operation (1-3): "))
            filepath = input("File path: ").strip()
            
            with open(filepath, 'rb') as f:
                data = f.read()
                
                if op == 1:
                    result = base64.b64encode(data).decode('utf-8')
                    print("\nBase64 Encoded:")
                elif op == 2:
                    result = base64.b64decode(data).decode('utf-8')
                    print("\nBase64 Decoded:")
                elif op == 3:
                    result = data.hex()
                    print("\nHex Dump:")
                else:
                    raise ValueError
                
                print("-" * 60)
                print(result[:500] + ("..." if len(result) > 500 else ""))
                print("-" * 60)
                
                if input("\nSave output? (y/n): ").lower() == "y":
                    with open(f"{filepath}.{'enc' if op==1 else 'dec'}", "w") as f:
                        f.write(result)
                    print("File saved")
        except Exception as e:
            print(f"! Error: {str(e)}")

    def unit_convert(self):
        """Unit Converter"""
        print("\n" + "=" * 30)
        print("UNIT CONVERTER".center(30))
        print("=" * 30)
        
        print("Supported units:")
        print("Length: km, miles, m, ft")
        print("Temperature: c/f or °C/°F")
        print("Weight: kg, lbs")
        
        try:
            value = float(input("Value: "))
            from_unit = input("From unit: ").lower().replace('°', '')
            to_unit = input("To unit: ").lower().replace('°', '')
            
            # Normalize temperature units
            if from_unit in ['c', 'f']:
                from_unit = '°' + from_unit
            if to_unit in ['c', 'f']:
                to_unit = '°' + to_unit
                
            conversions = {
                'length': {
                    'km': {'miles': 0.621371, 'm': 1000, 'ft': 3280.84},
                    'miles': {'km': 1.60934, 'm': 1609.34, 'ft': 5280},
                    'm': {'km': 0.001, 'miles': 0.000621371, 'ft': 3.28084},
                    'ft': {'m': 0.3048, 'km': 0.0003048, 'miles': 0.000189394}
                },
                'temp': {
                    '°c': {'°f': lambda c: c * 9/5 + 32},
                    '°f': {'°c': lambda f: (f - 32) * 5/9}
                },
                'weight': {
                    'kg': {'lbs': 2.20462},
                    'lbs': {'kg': 0.453592}
                }
            }
            
            converted = None
            for category in conversions.values():
                if from_unit in category and to_unit in category[from_unit]:
                    conv = category[from_unit][to_unit]
                    converted = conv(value) if callable(conv) else value * conv
                    break
            
            if converted is not None:
                # Display with proper unit symbols for temperature
                display_from = from_unit.replace('°', '°')
                display_to = to_unit.replace('°', '°')
                print(f"\n{value} {display_from} = {converted:.2f} {display_to}")
            else:
                print("! Unsupported conversion")
        except ValueError:
            print("! Invalid input")

    def system_info(self):
        """System Information"""
        print("\n" + "=" * 30)
        print("SYSTEM INFORMATION".center(30))
        print("=" * 30)
        
        print("OS:", platform.system(), platform.release())
        print("Architecture:", platform.machine())
        print("Processor:", platform.processor() or "Unknown")
        print("Python:", platform.python_version())

    def guython_interpreter(self):
        """Guython Interpreter"""
        print("\n" + "=" * 30)
        print("GUYTHON INTERPRETER".center(30))
        print("=" * 30)
        
        print("Enter Guython code line by line. Type 'exit' to quit.")
        
        # Try to find Guython in standard installation path
        guython_path = None
        default_path = os.path.expandvars(r"C:\Users\%USERNAME%\AppData\Local\Programs\Guython\guython.exe")
        
        # Check possible locations
        possible_paths = [
            default_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "guython.py"),
            os.path.join(os.path.dirname(__file__), "guython.py")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                guython_path = path
                break
            
        if not guython_path:
            print("! Error: Could not find Guython interpreter")
            print("Searched in:")
            for path in possible_paths:
                print(f"- {path}")
            return
        
        try:
            if guython_path.endswith('.exe'):
                # Run as executable - launch interactive mode
                print(f"\nLaunching Guython at: {guython_path}")
                os.system(f'"{guython_path}"')
            else:
                # Run as Python module
                sys.path.insert(0, os.path.dirname(guython_path))
                from guython import GuythonInterpreter
                interpreter = GuythonInterpreter()
                while True:
                    try:
                        code = input(">>> ").strip()
                        if code.lower() in ('exit', 'quit'):
                            break
                        interpreter.run_line(code)
                    except KeyboardInterrupt:
                        print("\n(Use 'exit' or 'quit' to exit)")
                    except Exception as e:
                        print(f"Error: {e}")
        except Exception as e:
            print(f"! Error running Guython: {str(e)}")

    def qr_code(self):
        """QR Code Generator"""
        print("\n" + "=" * 30)
        print("QR CODE GENERATOR".center(30))
        print("=" * 30)
        
        try:
            import qrcode
            data = input("Enter text/URL to encode: ")
            filename = input("Save as (e.g., qr.png): ").strip() or "qr.png"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filename)
            print(f"QR code saved as {filename}")
            
            if input("Show QR code? (y/n): ").lower() == "y":
                if sys.platform == "win32":
                    os.startfile(filename)
                else:
                    webbrowser.open(filename)
        except ImportError:
            print("! Install qrcode first: pip install qrcode[pil]")

    def checksum(self):
        """Checksum Calculator"""
        print("\n" + "=" * 30)
        print("CHECKSUM CALCULATOR".center(30))
        print("=" * 30)
        
        filepath = input("File path: ").strip()
        if not os.path.exists(filepath):
            print("! File not found")
            return
            
        algorithm = input("Algorithm (md5/sha1/sha256): ").lower()
        valid_algs = ['md5', 'sha1', 'sha256']
        
        if algorithm not in valid_algs:
            print(f"! Invalid algorithm. Choose from {', '.join(valid_algs)}")
            return
            
        try:
            hasher = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            print(f"\n{algorithm.upper()}: {hasher.hexdigest()}")
        except Exception as e:
            print(f"! Error: {str(e)}")

    def text_to_speech(self):
        """Text to Speech"""
        print("\n" + "=" * 30)
        print("TEXT TO SPEECH".center(30))
        print("=" * 30)
        
        try:
            from gtts import gTTS
            import playsound
            
            text = input("Enter text: ")
            filename = "speech.mp3"
            
            tts = gTTS(text=text, lang='en')
            tts.save(filename)
            print(f"Saved as {filename}")
            
            if input("Play audio? (y/n): ").lower() == "y":
                playsound.playsound(filename)
                os.remove(filename)  # Clean up
        except ImportError:
            print("! Install dependencies first:")
            print("pip install gtts playsound")

    def directory_lister(self):
        """Directory Lister"""
        print("\n" + "=" * 30)
        print("DIRECTORY LISTER".center(30))
        print("=" * 30)
        
        path = input("Directory path [.]: ").strip() or "."
        if not os.path.exists(path):
            print("! Path not found")
            return
            
        print(f"\nContents of {os.path.abspath(path)}:")
        print("-" * 60)
        for i, item in enumerate(os.listdir(path), 1):
            fullpath = os.path.join(path, item)
            size = os.path.getsize(fullpath) if os.path.isfile(fullpath) else 0
            mtime = datetime.fromtimestamp(os.path.getmtime(fullpath))
            print(f"{i:3}. {item:<40} {size:>10,} bytes  {mtime:%Y-%m-%d %H:%M}")
        print("-" * 60)
        
        if input("\nSave to file? (y/n): ").lower() == "y":
            with open("directory.txt", "w") as f:
                f.write(f"Directory of {os.path.abspath(path)}\n")
                f.write("-" * 60 + "\n")
                for item in os.listdir(path):
                    f.write(f"{item}\n")
            print("Saved to directory.txt")

    def web_search(self):
        """Web Search"""
        print("\n" + "=" * 30)
        print("WEB SEARCH".center(30))
        print("=" * 30)
        
        query = input("Search query: ")
        if not query:
            print("! Query cannot be empty")
            return
            
        engine = input("Engine (google/bing/yahoo/duckduckgo): ").lower() or "google"
        url = {
            "google": f"https://www.google.com/search?q={query}",
            "bing": f"https://www.bing.com/search?q={query}",
            "yahoo": f"https://search.yahoo.com/search?p={query}",
            "duckduckgo": f"https://duckduckgo.com/?q={query}"
        }.get(engine, f"https://www.google.com/search?q={query}")
        
        print(f"\nOpening: {url}")
        webbrowser.open(url)

    def zip_tool(self):
        """Zip/Unzip Tool"""
        print("\n" + "=" * 30)
        print("ZIP TOOL".center(30))
        print("=" * 30)
        
        print("1. Create ZIP\n2. Extract ZIP")
        choice = input("Select operation: ").strip()
        
        if choice == "1":
            files = input("Files/dirs to zip (comma separated): ").split(',')
            files = [f.strip() for f in files if f.strip()]
            zipname = input("Output zip name: ").strip() or "archive.zip"
            
            try:
                with zipfile.ZipFile(zipname, 'w') as zipf:
                    for file in files:
                        if os.path.isdir(file):
                            for root, _, files in os.walk(file):
                                for f in files:
                                    zipf.write(os.path.join(root, f))
                        else:
                            zipf.write(file)
                print(f"Created {zipname}")
            except Exception as e:
                print(f"! Error: {str(e)}")
                
        elif choice == "2":
            zipname = input("ZIP file to extract: ").strip()
            dest = input("Destination dir [.]: ").strip() or "."
            
            try:
                with zipfile.ZipFile(zipname, 'r') as zipf:
                    zipf.extractall(dest)
                print(f"Extracted to {os.path.abspath(dest)}")
            except Exception as e:
                print(f"! Error: {str(e)}")
        else:
            print("! Invalid choice")

    def exit_tool(self):
        """Graceful exit"""
        print("\nClosing Guy's Multitool...")
        for i in range(3, 0, -1):
            print(f"Exiting in {i}...", end='\r')
            sleep(1)
        print("Thank you for using Guy's Multitool!")
        sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    try:
        GuysMultitool().run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
