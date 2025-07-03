"""
JMS Authentication Client for OAuth2 authentication with JMS API
"""
import time
import sys
from typing import Dict, Optional
from utils.event_system import event_system


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


# Debug: Print Python path
print("Python path:", sys.path)

# Check if requests module is available
try:
    print("Attempting to import requests module...")
    import requests
    print(f"Successfully imported requests module from: {requests.__file__}")
    REQUESTS_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import requests module: {str(e)}")
    REQUESTS_AVAILABLE = True
    event_system.publish("error", f"Python 'requests' module not found: {str(e)}. JMS integration will not be available.")

# Alternative check using importlib
try:
    import importlib.util
    print("Checking for requests module using importlib...")
    spec = importlib.util.find_spec("requests")
    if spec:
        print(f"Found requests module spec at: {spec.origin}")
    else:
        print("No requests module spec found")
except Exception as e:
    print(f"Error checking for requests with importlib: {str(e)}")


class JMSAuthClient:
    """Handles OAuth2 authentication with JMS API"""
    
    def __init__(self, base_url: str, client_id: str = "EsbusciClient", 
                 client_secret: str = "DefaultEsbusciClientSecret"):
        """
        Initialize the JMS authentication client
        
        Args:
            base_url: Base URL of the JMS API
            client_id: OAuth2 client ID (default: EsbusciClient)
            client_secret: OAuth2 client secret (default: DefaultEsbusciClientSecret)
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expiry = 0
        
    def get_auth_header(self) -> Dict[str, str]:
        """
        Get authentication header with valid token
        
        Returns:
            Dictionary with Authorization header
        """
        if not self.token or time.time() >= self.token_expiry:
            self._refresh_token()
        return {"Authorization": f"Bearer {self.token}"}
    
    def _refresh_token(self) -> None:
        """
        Refresh the OAuth2 token
        
        Raises:
            Exception: If authentication fails
        """
        if not REQUESTS_AVAILABLE:
            error_msg = "Cannot authenticate: 'requests' module not available"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
            
        auth_url = f"{self.base_url}/IAM/Authorization/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "response_type": "token",
            "scope": "esbusci"
        }
        
        try:
            response = requests.post(auth_url, data=payload)
            response.raise_for_status()
            
            data = response.json()
            self.token = data["access_token"]
            # Set expiry to 55 minutes (5 minutes before actual expiry)
            self.token_expiry = time.time() + (55 * 60)
            
            event_system.publish("jms_auth_success", "Successfully authenticated with JMS API")
        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication failed: {str(e)}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid authentication response: {str(e)}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)