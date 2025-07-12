#!/usr/bin/env python3
"""
Setup and installation script for NC Parser
"""

import subprocess
import sys
import os

def install_packages():
    """Install required packages."""
    packages = [
        "numpy>=1.21.0",
        "matplotlib>=3.5.0", 
        "open3d>=0.15.0",
        "pandas>=1.3.0",
        "plotly>=5.0.0",
        "regex>=2021.0.0"
    ]
    
    print("Installing required packages...")
    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"Warning: Failed to install {package}")
    
    print("Package installation completed!")

def test_installation():
    """Test if all packages are properly installed."""
    print("\nTesting installation...")
    
    try:
        import numpy
        print(f"✓ NumPy {numpy.__version__}")
    except ImportError:
        print("✗ NumPy not available")
        return False
    
    try:
        import matplotlib
        print(f"✓ Matplotlib {matplotlib.__version__}")
    except ImportError:
        print("✗ Matplotlib not available")
        return False
    
    try:
        import open3d
        print(f"✓ Open3D {open3d.__version__}")
    except ImportError:
        print("✗ Open3D not available")
        return False
    
    try:
        import plotly
        print(f"✓ Plotly {plotly.__version__}")
    except ImportError:
        print("✗ Plotly not available")
        return False
    
    try:
        import pandas
        print(f"✓ Pandas {pandas.__version__}")
    except ImportError:
        print("✗ Pandas not available")
        return False
    
    try:
        import regex
        print(f"✓ Regex module available")
    except ImportError:
        print("✗ Regex not available")
        return False
    
    return True

def main():
    """Main setup function."""
    print("NC Parser Setup Script")
    print("=" * 30)
    
    # Install packages
    install_packages()
    
    # Test installation
    if test_installation():
        print("\n✓ All packages installed successfully!")
        print("\nYou can now use the NC Parser:")
        print("  python demo.py          - Run demo")
        print("  python test_basic.py    - Test basic functionality")  
        print("  python main.py --help   - See all options")
        print("  python main.py --create-sample - Create and process sample file")
    else:
        print("\n✗ Some packages failed to install.")
        print("Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
