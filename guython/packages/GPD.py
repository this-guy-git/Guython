# gpd code
import os
import shutil
import json
import requests
import subprocess
import importlib.util
import sys
import time
from urllib.parse import urljoin
from types import SimpleNamespace
from typing import Dict, List, Optional
# Import exceptions from guython.py
try:
    from guython import GuythonError, GuythonRuntimeError
except ImportError:
    # Fallback definitions if running standalone
    class GuythonError(Exception):
        """Base exception for Guython errors"""
        pass
    
    class GuythonRuntimeError(GuythonError):
        """Runtime error in Guython code"""
        pass

class GPD:
    """Guython Package Database Manager"""
    
    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.base_url = "https://github.com/this-guy-git/guython-packages/blob/main/packages?t={int(time.time())}"
        self.raw_base = f"https://raw.githubusercontent.com/this-guy-git/guython-packages/main/packages/?t={int(time.time())}"
        self.local_pkg_dir = os.getcwd() + "/packages"
        self.index_file = os.path.join(self.local_pkg_dir, "gpd_index.json")
        
        # Initialize package system
        os.makedirs(self.local_pkg_dir, exist_ok=True)
        self.package_index = self._load_index()
        
    
    def _get_package_language(self, pkg_name: str) -> str:
        """Fetch manifest.gy from GitHub to determine package language"""
        manifest_url = urljoin(self.raw_base, f"{pkg_name}/manifest.gy")
        try:
            response = requests.get(manifest_url, timeout=10)
            response.raise_for_status()
            for line in response.text.splitlines():
                if line.strip().startswith("language="):
                    lang = line.split("=")[1].strip().strip('"\'')
                    return lang.lower()
        except requests.RequestException:
            pass
        return "python"  # Default to Python if manifest missing/unreadable
    
    def _load_index(self) -> Dict:
        """Load local package index"""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_index(self):
        """Save package index to disk"""
        with open(self.index_file, 'w') as f:
            json.dump(self.package_index, f, indent=2)
    
    def _fetch_remote_index(self) -> Dict:
        """Get the latest package index from GitHub"""
        try:
            url = urljoin(self.raw_base, "index.json")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise GuythonRuntimeError(f"Failed to fetch package index: {str(e)}")
    
    def install(self, pkg_name: str):
        """Install a package from the GPD repository"""
        try:
            if pkg_name in self.package_index:
                print(f"Package {pkg_name} is already installed")
                return
    
            # Get package metadata
            remote_index = self._fetch_remote_index()
            if pkg_name not in remote_index:
                raise GuythonRuntimeError(f"Package not found: {pkg_name}")
            pkg_data = remote_index[pkg_name]
    
            # 1. Get the manifest FIRST
            manifest_url = urljoin(self.raw_base, f"{pkg_name}/manifest.gy")
            try:
                response = requests.get(manifest_url, timeout=10)
                response.raise_for_status()
                manifest = response.text
                language = "python"  # Default fallback
                
                for line in manifest.splitlines():
                    if line.strip().startswith("language="):
                        language = line.split("=")[1].strip().strip('"\'').lower()
                        break
            except requests.RequestException:
                language = "python"  # Default if manifest missing
    
            # 2. Verify valid language
            if language not in ("python", "guython"):
                language = "python"  # Force to python if invalid
    
            # 3. Create package directory
            pkg_dir = os.path.join(self.local_pkg_dir, pkg_name)
            os.makedirs(pkg_dir, exist_ok=True)
    
            # 4. Download ALL files
            downloaded_files = []
            for file_path in pkg_data['files']:
                file_url = urljoin(self.raw_base, f"{pkg_name}/{file_path}")
                try:
                    response = requests.get(file_url, timeout=10)
                    response.raise_for_status()
                    
                    dest_path = os.path.join(pkg_dir, file_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    with open(dest_path, 'wb') as f:
                        f.write(response.content)
                    downloaded_files.append(file_path)
                    print(f"✓ Downloaded: {file_path}")
                except requests.RequestException as e:
                    print(f"Warning: Failed to download {file_path}: {str(e)}")
    
            # 5. Find the main file
            main_base = pkg_data.get('main', 'main')
            possible_mains = [
                f"{main_base}.py",
                f"{main_base}.gy",
                "main.py",
                "main.gy",
                f"{pkg_name}.py",
                f"{pkg_name}.gy"
            ]
            
            main_file = None
            for candidate in possible_mains:
                if os.path.exists(os.path.join(pkg_dir, candidate)):
                    main_file = candidate
                    break
                
            if not main_file:
                # Try to find any .py or .gy file
                all_files = os.listdir(pkg_dir)
                for f in all_files:
                    if f.endswith('.py') or f.endswith('.gy'):
                        main_file = f
                        break
                    
            if not main_file:
                raise GuythonRuntimeError(
                    f"No main file found in package {pkg_name}\n"
                    f"Downloaded files: {downloaded_files}\n"
                    f"Tried: {possible_mains}"
                )
    
            # 6. Update index
            self.package_index[pkg_name] = {
                'version': pkg_data['version'],
                'main': os.path.splitext(main_file)[0],  # Remove extension
                'language': language,
                'files': downloaded_files
            }
            self._save_index()
            
            print(f"✓ Successfully installed {pkg_name} v{pkg_data['version']}")
            print(f"Main file: {main_file}")
            
        except Exception as e:
            if 'pkg_dir' in locals() and os.path.exists(pkg_dir):
                shutil.rmtree(pkg_dir)
            raise GuythonRuntimeError(f"Installation failed: {str(e)}")

    def _import_package(self, pkg_name: str, alias: Optional[str] = None):
        """Import a package using the correct file extension"""
        if pkg_name not in self.package_index:
            raise GuythonRuntimeError(f"Package not installed: {pkg_name}")

        pkg_data = self.package_index[pkg_name]
        pkg_dir = os.path.join(self.local_pkg_dir, pkg_name)
        main_base = pkg_data['main']
        language = pkg_data.get('language', 'python')  # Default to python, not guython

        # Determine the correct extension
        ext = '.py' if language == 'python' else '.gy'
        main_file = f"{main_base}{ext}"
        main_path = os.path.join(pkg_dir, main_file)

        # Fallback if exact file not found
        if not os.path.exists(main_path):
            # Try to find files with the main_base prefix
            found_files = [f for f in os.listdir(pkg_dir) if f.startswith(main_base)]
            if found_files:
                main_file = found_files[0]
                main_path = os.path.join(pkg_dir, main_file)
                print(f"Warning: Using {main_file} instead of {main_base}{ext}")
            else:
                # Try to find any .py or .gy file as last resort
                all_files = [f for f in os.listdir(pkg_dir) if f.endswith('.py') or f.endswith('.gy')]
                if all_files:
                    main_file = all_files[0]
                    main_path = os.path.join(pkg_dir, main_file)
                    print(f"Warning: Using {main_file} as no main file found")
                else:
                    raise GuythonRuntimeError(f"No main file found in package {pkg_name}")

        # Determine language from actual file extension if not set properly
        if main_file.endswith('.py'):
            return self._import_python_package(pkg_name, main_path, alias)
        else:
            return self._import_guython_package(pkg_name, main_path, alias)

    def _import_python_package(self, pkg_name: str, py_path: str, alias: Optional[str] = None):
        """Safely import a Python package into Guython"""
        try:
            # Create a module specification
            spec = importlib.util.spec_from_file_location(pkg_name, py_path)
            module = importlib.util.module_from_spec(spec)
            
            # Create safe execution environment
            unsafe_modules = {
                'ctypes',
                'cffi',
                'marshal',
                'pickle',
                'importlib',
            }
            
            # Define safe import function
            def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
                if name in unsafe_modules:
                    raise ImportError(f"Module '{name}' not allowed in Guython packages")
                return __import__(name, globals, locals, fromlist, level)
            
            
            safe_globals = {
                '__builtins__': {
                    'None': None,
                    'True': True,
                    'False': False,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'tuple': tuple,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'len': len,
                    'range': range,
                    'print': print,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'reversed': reversed,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'any': any,
                    'all': all,
                    '__import__': safe_import,
                },
                '__name__': pkg_name,
                '__file__': py_path,
            }
            
            # Add safe modules directly to globals so they're available
            
            # Read and compile the code
            with open(py_path, 'r') as f:
                code = f.read()
            
            # Check for dangerous operations (specific dangerous calls)
            dangerous_patterns = [
                'eval(', 'exec(', 
                'open(', 'file(', 
                'os.system', 'os.spawn',
                'subprocess.', 'sys.path',
                'importlib.import_module'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in code:
                    raise GuythonRuntimeError(f"Unsafe operation found: {pattern}")
            
            # Execute in restricted environment
            compiled = compile(code, py_path, 'exec')
            
            # Create a combined namespace that includes both safe_globals and module.__dict__
            exec_namespace = safe_globals.copy()
            exec_namespace.update(module.__dict__)
            
            exec(compiled, exec_namespace)
            
            # Copy back the results to the module
            for key, value in exec_namespace.items():
                if not key.startswith('__') and key not in safe_globals:
                    setattr(module, key, value)
            
            # Add to Guython variables
            var_name = alias or pkg_name
            self.interpreter.variables[var_name] = module
            
            print(f"Imported Python package: {pkg_name}")
            print(f"Available functions: {[attr for attr in dir(module) if not attr.startswith('_')]}")
            return module
        except Exception as e:
            raise GuythonRuntimeError(f"Error importing Python package: {e}")
    
    def _import_guython_package(self, pkg_name: str, gy_path: str, alias: Optional[str] = None):
        """Import a Guython package"""
        try:
            if pkg_name not in self.package_index:
                raise GuythonRuntimeError(f"Package not installed: {pkg_name}")
            
            # Create namespace
            var_name = alias or pkg_name
            self.interpreter.variables[var_name] = SimpleNamespace()
            
            # Execute in package context
            old_vars = self.interpreter.variables.copy()
            self.interpreter.variables = self.interpreter.variables[var_name].__dict__
            
            try:
                with open(gy_path, 'r') as f:
                    self.interpreter.run_program(f.read().splitlines())
            finally:
                # Restore original variables
                self.interpreter.variables = old_vars
                
            print(f"Imported Guython package: {pkg_name}")
        except Exception as e:
            raise GuythonRuntimeError(f"Import failed: {str(e)}")
    
    def import_pkg(self, pkg_name: str, alias: Optional[str] = None):
        """Public method to import a package"""
        return self._import_package(pkg_name, alias)
    
    def list_packages(self) -> List[str]:
        """List all installed packages"""
        return list(self.package_index.keys())
    
    def uninstall(self, pkg_name: str):
        """Remove an installed package"""
        try:
            if pkg_name not in self.package_index:
                print(f"Package not installed: {pkg_name}")
                return
            
            pkg_dir = os.path.join(self.local_pkg_dir, pkg_name)
            
            # Remove package files
            try:
                if os.name == 'nt':  # Windows
                    subprocess.run(f'rmdir /S /Q "{pkg_dir}"', shell=True, check=True)
                else:  # Unix-like
                    subprocess.run(['rm', '-rf', pkg_dir], check=True)
            except subprocess.CalledProcessError:
                raise GuythonRuntimeError(f"Failed to remove package files")
            
            # Update index
            del self.package_index[pkg_name]
            self._save_index()
            print(f"Successfully uninstalled {pkg_name}")
        except Exception as e:
            raise GuythonRuntimeError(f"Uninstall failed: {str(e)}")

    def check_updates(self):
        try:
            remote_index = self._fetch_remote_index()
        except GuythonRuntimeError as e:
            print(f"Could not fetch remote index: {e}")
            return
    
        updates_found = False
        for pkg, data in self.package_index.items():
            current_version = data.get('version', '0.0.0')
            remote_version = remote_index.get(pkg, {}).get('version')
            if remote_version is None:
                print(f"{pkg}: Not found in remote repository")
                continue
            
            if remote_version != current_version:
                print(f"{pkg}: {current_version} -> {remote_version} (Update available)")
                updates_found = True
            else:
                print(f"{pkg}: {current_version} (Up to date)")
    
        if not updates_found:
            print("All packages are up to date.")

    def update_package(self, pkg_name: str):
        if pkg_name not in self.package_index:
            print(f"Package '{pkg_name}' is not installed.")
            return

        try:
            remote_index = self._fetch_remote_index()
        except GuythonRuntimeError as e:
            print(f"Could not fetch remote index: {e}")
            return

        current_version = self.package_index[pkg_name].get('version', '0.0.0')
        remote_version = remote_index.get(pkg_name, {}).get('version')

        if remote_version is None:
            print(f"Package '{pkg_name}' not found in remote repository.")
            return

        if current_version == remote_version:
            print(f"'{pkg_name}' is already up to date.")
            return

        print(f"Updating '{pkg_name}' from {current_version} to {remote_version}...")

        # Remove old files
        pkg_dir = os.path.join(self.local_pkg_dir, pkg_name)
        if os.path.exists(pkg_dir):
            shutil.rmtree(pkg_dir)

        if pkg_name in self.package_index:
            del self.package_index[pkg_name]
            self._save_index()

        try:
            self.install(pkg_name)

            # 🛠️ Force update local index from remote
            new_data = remote_index[pkg_name]
            self.package_index[pkg_name]['version'] = new_data.get('version', remote_version)
            self._save_index()

            print(f"'{pkg_name}' updated successfully.")
        except GuythonRuntimeError as e:
            print(f"Update failed: {e}")
