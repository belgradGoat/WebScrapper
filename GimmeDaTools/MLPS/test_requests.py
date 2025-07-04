#!/usr/bin/env python3
"""
Test script to check if the requests module is available
"""
import sys
import importlib.util

def main():
    """Main function"""
    print("Python version:", sys.version)
    print("Python executable:", sys.executable)
    print("Python path:")
    for path in sys.path:
        print(f"  - {path}")
    
    print("\nChecking for requests module...")
    
    # Check using importlib
    spec = importlib.util.find_spec("requests")
    if spec:
        print(f"Found requests module spec at: {spec.origin}")
        
        # Try to import it
        try:
            import requests
            print(f"Successfully imported requests module from: {requests.__file__}")
            print(f"Requests version: {requests.__version__}")
            print("Requests is available!")
        except ImportError as e:
            print(f"Error importing requests: {str(e)}")
    else:
        print("No requests module spec found")
        print("Requests is NOT available!")
    
    # Try to make a simple request
    try:
        import requests
        print("\nTrying to make a test request to httpbin.org...")
        response = requests.get("https://httpbin.org/get", timeout=5)
        print(f"Request successful! Status code: {response.status_code}")
    except Exception as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    main()