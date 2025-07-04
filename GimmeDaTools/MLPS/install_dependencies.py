#!/usr/bin/env python3
"""
Install required dependencies for NC Tool Analyzer
"""
import sys
import subprocess
import importlib.util
import os

def check_module(module_name):
    """Check if a module is installed"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False
        return True
    except (ImportError, AttributeError):
        return False

def install_module(module_name):
    """Install a module using pip"""
    print(f"Installing {module_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
        print(f"Successfully installed {module_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install {module_name}: {e}")
        return False

def main():
    """Main function"""
    print("Checking dependencies...")
    
    # Check if requests is installed
    if not check_module("requests"):
        print("requests module not found")
        if not install_module("requests"):
            print("Failed to install requests module")
            print("You can install it manually using:")
            print("pip install requests")
            return False
    else:
        print("requests module already installed")
    
    print("All dependencies installed")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Ask if user wants to run the application
    if input("Do you want to run the application now? (y/n): ").lower() == "y":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(script_dir, "main.py")
        subprocess.call([sys.executable, main_script])