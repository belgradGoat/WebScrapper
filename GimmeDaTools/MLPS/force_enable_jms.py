#!/usr/bin/env python3
"""
Script to force enable JMS integration for testing
"""
import os
import sys

def main():
    """Main function"""
    # Path to jms_auth.py
    jms_auth_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "services", "jms", "jms_auth.py"
    )
    
    # Check if file exists
    if not os.path.exists(jms_auth_path):
        print(f"Error: {jms_auth_path} not found")
        return
    
    # Read the file
    with open(jms_auth_path, "r") as f:
        content = f.read()
    
    # Replace the REQUESTS_AVAILABLE check
    if "REQUESTS_AVAILABLE = " in content:
        content = content.replace(
            "REQUESTS_AVAILABLE = False",
            "REQUESTS_AVAILABLE = True"
        )
        content = content.replace(
            "REQUESTS_AVAILABLE = spec is not None",
            "REQUESTS_AVAILABLE = True"
        )
        
        # Add mock requests module if needed
        if "class MockRequests:" not in content:
            mock_code = """
# Mock requests module for testing
class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = str(json_data)
        
    def json(self):
        return self._json_data
        
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP Error: {self.status_code}")

class MockRequests:
    @staticmethod
    def get(url, **kwargs):
        print(f"Mock GET request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})
        
    @staticmethod
    def post(url, **kwargs):
        print(f"Mock POST request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})
        
    @staticmethod
    def put(url, **kwargs):
        print(f"Mock PUT request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})
        
    @staticmethod
    def patch(url, **kwargs):
        print(f"Mock PATCH request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})
        
    @staticmethod
    def delete(url, **kwargs):
        print(f"Mock DELETE request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})
        
    @staticmethod
    def request(method, url, **kwargs):
        print(f"Mock {method} request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})

# Use mock requests if real one is not available
try:
    import requests
    print(f"Using real requests module from: {requests.__file__}")
except ImportError:
    print("Using mock requests module")
    requests = MockRequests
    REQUESTS_AVAILABLE = True
"""
            # Find a good place to insert the mock code
            if "# Import requests if available" in content:
                content = content.replace(
                    "# Import requests if available",
                    "# Import requests if available\n" + mock_code
                )
            else:
                # Add it after the imports
                import_end = content.find("from utils.event_system import event_system") + len("from utils.event_system import event_system")
                content = content[:import_end] + "\n\n" + mock_code + content[import_end:]
    
        # Write the modified content back
        with open(jms_auth_path, "w") as f:
            f.write(content)
            
        print(f"Successfully modified {jms_auth_path}")
        print("JMS integration has been force enabled with a mock requests module")
        print("You can now run the application and test the JMS integration")
    else:
        print(f"Could not find REQUESTS_AVAILABLE in {jms_auth_path}")

if __name__ == "__main__":
    main()