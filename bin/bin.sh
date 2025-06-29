#!/bin/bash

# Root directory
mkdir -p guython/core
mkdir -p guython/utils
mkdir -p guython/packages

# Create __init__.py files
touch guython/__init__.py
touch guython/core/__init__.py
touch guython/utils/__init__.py
touch guython/packages/__init__.py

# Core files
touch guython/core/interpreter.py
touch guython/core/evaluator.py
touch guython/core/gui.py
touch guython/core/errors.py
touch guython/core/constants.py

# Utils
touch guython/utils/fileio.py

# Main entry
touch guython/main.py
touch run_guython.py

# Done
echo "Guython 2 structure created successfully!"
