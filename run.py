import sys
import os

from guython.core.interpreter import GuythonInterpreter
from guython.core.constants import VERSION

from guython.core.update import check_for_updates

def main():
    interpreter = GuythonInterpreter()

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        if not (filename.endswith('.gy') or filename.endswith('.guy')):
            print("Error: Invalid file type. File must be .gy or .guy")
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
        # Interactive CLI mode
        print(f"Guython Interpreter {VERSION}")
        print("Type 'exit' to quit, 'debug' to toggle debug mode, 'vars' to show variables.")
        check_for_updates()

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
                    for name, val in interpreter.get_variables().items():
                        print(f"  {name} = {val}")
                    continue
                elif line.startswith("guython "):
                    filename = line[8:].strip()
                    if not (filename.endswith('.gy') or filename.endswith('.guy')):
                        print("Error: Invalid file type.")
                        continue
                    if not os.path.isfile(filename):
                        print(f"Error: File not found: {filename}")
                        continue
                    with open(filename, 'r') as f:
                        interpreter.run_program(f.readlines())
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
