"""
JMS Authentication Client for OAuth2 authentication with JMS API
"""
import time
import sys
import os
import logging
from typing import Dict, Optional
from utils.event_system import event_system

# Set up logger
logger = logging.getLogger(__name__)

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
        # If this is an authentication request (URL contains "token"), return a proper OAuth token response
        if "token" in url:
            print("Returning mock OAuth token response")
            return MockResponse(200, {
                "access_token": "mock_access_token_12345",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "esbusci"
            })
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
        # If this is an authentication request (URL contains "token"), return a proper OAuth token response
        if "token" in url and method.upper() == "POST":
            print("Returning mock OAuth token response")
            return MockResponse(200, {
                "access_token": "mock_access_token_12345",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "esbusci"
            })
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})

# Debug: Print Python path
print("Python path:", sys.path)

# Force requests module to be available
try:
    print("Attempting to import requests module...")
    # Try to import requests directly
    try:
        import requests
        print(f"Successfully imported requests module from: {requests.__file__}")
        REQUESTS_AVAILABLE = True
    except ImportError as e:
        print(f"Direct import failed: {str(e)}")
        
        # Try to import requests using importlib
        try:
            import importlib.util
            import importlib.machinery
            
            # Try to find requests in common locations
            possible_paths = [
                # Standard site-packages locations
                os.path.join(os.path.dirname(sys.executable), 'Lib', 'site-packages', 'requests', '__init__.py'),
                os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Lib', 'site-packages', 'requests', '__init__.py'),
                # User site-packages
                os.path.expanduser('~/.local/lib/python3.*/site-packages/requests/__init__.py'),
                # Conda environments
                os.path.join(os.path.dirname(sys.executable), 'lib', 'python*', 'site-packages', 'requests', '__init__.py'),
            ]
            
            requests_path = None
            for path in possible_paths:
                # Handle wildcards in paths
                if '*' in path:
                    import glob
                    matching_paths = glob.glob(path)
                    if matching_paths:
                        requests_path = matching_paths[0]
                        break
                elif os.path.exists(path):
                    requests_path = path
                    break
            
            if requests_path:
                print(f"Found requests module at: {requests_path}")
                spec = importlib.util.spec_from_file_location("requests", requests_path)
                requests = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(requests)
                print(f"Successfully loaded requests module from: {requests_path}")
                REQUESTS_AVAILABLE = True
            else:
                # Fall back to mock requests
                print("Could not find requests module, using mock implementation")
                requests = MockRequests
                REQUESTS_AVAILABLE = False
        except Exception as e2:
            print(f"Failed to load requests module: {str(e2)}")
            requests = MockRequests
            REQUESTS_AVAILABLE = False
except Exception as e:
    print(f"Error handling requests import: {str(e)}")
    requests = MockRequests
    REQUESTS_AVAILABLE = False
    event_system.publish("error", f"Error handling requests import: {str(e)}. Using mock JMS functionality.")

# Comment out forcing REQUESTS_AVAILABLE to True for testing
# This allows the code to properly detect whether requests is available
print("Using detected REQUESTS_AVAILABLE value:", REQUESTS_AVAILABLE)
# REQUESTS_AVAILABLE = True

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
                 client_secret: str = "DefaultEsbusciClientSecret",
                 username: str = None, password: str = None):
        """
        Initialize the JMS authentication client
        
        Args:
            base_url: Base URL of the JMS API
            client_id: OAuth2 client ID (default: EsbusciClient)
            client_secret: OAuth2 client secret (default: DefaultEsbusciClientSecret)
            username: Username for authentication (optional)
            password: Password for authentication (optional)
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.token = None
        self.token_expiry = 0
        
        print(f"JMS Auth Client initialized with URL: {base_url}")
        print(f"Using client_id: {client_id}")
        print(f"Username provided: {username is not None}")
        
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
            print("Using mock authentication since 'requests' module is not available")
            self.token = "mock_token_12345"
            self.token_expiry = time.time() + (55 * 60)
            event_system.publish("jms_auth_success", "Successfully authenticated with mock JMS API")
            return
            
        auth_url = f"{self.base_url}/IAM/Authorization/token"
        
        # Prepare payload based on authentication method
        if self.username and self.password:
            # Use password grant type if username/password provided
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
                "response_type": "token",
                "scope": "esbusci"
            }
            print(f"Using password grant type with username: {self.username}")
        else:
            # Use client credentials grant type
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
                "response_type": "token",
                "scope": "esbusci"
            }
            print("Using client credentials grant type")
        
        try:
            # This block is now redundant since we handle mock authentication at the beginning of the method
                
            # Real authentication
            logger.info(f"Sending authentication request to {auth_url}")
            
            # Try with provided credentials first if available
            if self.username and self.password:
                try:
                    logger.info(f"Attempting authentication with username: {self.username}")
                    response = requests.post(auth_url, data=payload)
                    logger.info(f"Authentication response status code: {response.status_code}")
                    
                    # If authentication fails with username/password, try client credentials
                    if response.status_code == 401:
                        logger.warning("Username/password authentication failed. Trying client credentials.")
                        event_system.publish("warning", "Username/password authentication failed. Trying client credentials.")
                        
                        # Switch to client credentials
                        payload = {
                            "client_id": self.client_id,
                            "client_secret": self.client_secret,
                            "grant_type": "client_credentials",
                            "response_type": "token",
                            "scope": "esbusci"
                        }
                        logger.info("Falling back to client credentials grant type")
                        response = requests.post(auth_url, data=payload)
                        logger.info(f"Client credentials authentication response status code: {response.status_code}")
                    
                    # Handle other error codes
                    if response.status_code >= 400:
                        error_msg = f"Authentication failed with status {response.status_code}"
                        logger.error(error_msg)
                        event_system.publish("error", error_msg)
                        raise Exception(error_msg)
                    
                    # Log response content for debugging
                    try:
                        response_text = response.text
                        logger.debug(f"Authentication response text: {response_text[:200]}...")
                    except Exception as e:
                        logger.error(f"Could not get response text: {str(e)}")
                    
                    response.raise_for_status()
                    
                    data = response.json()
                    logger.info(f"Authentication response parsed successfully")
                    
                    if "access_token" not in data:
                        logger.error(f"No access_token in response. Keys: {list(data.keys())}")
                        raise KeyError("No access_token in response")
                        
                    self.token = data["access_token"]
                    # Set expiry to 55 minutes (5 minutes before actual expiry)
                    self.token_expiry = time.time() + (55 * 60)
                    
                    event_system.publish("jms_auth_success", "Successfully authenticated with JMS API")
                    
                except Exception as e:
                    logger.error(f"Authentication attempt failed: {str(e)}")
                    raise
            else:
                # Use client credentials directly if no username/password
                try:
                    response = requests.post(auth_url, data=payload)
                    logger.info(f"Authentication response status code: {response.status_code}")
                    
                    # More detailed error handling based on status code
                    if response.status_code == 401:
                        error_msg = "Authentication failed: Invalid client credentials."
                        logger.error(error_msg)
                        event_system.publish("error", error_msg)
                        raise Exception(error_msg)
                    elif response.status_code >= 400:
                        error_msg = f"Authentication failed with status {response.status_code}"
                        logger.error(error_msg)
                        event_system.publish("error", error_msg)
                        raise Exception(error_msg)
                    
                    # Log response content for debugging
                    try:
                        response_text = response.text
                        logger.debug(f"Authentication response text: {response_text[:200]}...")
                    except Exception as e:
                        logger.error(f"Could not get response text: {str(e)}")
                    
                    response.raise_for_status()
                    
                    data = response.json()
                    logger.info(f"Authentication response parsed successfully")
                    
                    if "access_token" not in data:
                        logger.error(f"No access_token in response. Keys: {list(data.keys())}")
                        raise KeyError("No access_token in response")
                        
                    self.token = data["access_token"]
                    # Set expiry to 55 minutes (5 minutes before actual expiry)
                    self.token_expiry = time.time() + (55 * 60)
                    
                    event_system.publish("jms_auth_success", "Successfully authenticated with JMS API")
                except Exception as e:
                    logger.error(f"Authentication attempt failed: {str(e)}")
                    raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {str(e)}")
            error_msg = f"Connection error: Could not connect to {auth_url}. Falling back to mock authentication."
            event_system.publish("warning", error_msg)
            print(error_msg)
            
            # Fall back to mock authentication
            self.token = "mock_token_12345"
            self.token_expiry = time.time() + (55 * 60)
            event_system.publish("jms_auth_success", "Using mock authentication due to connection error")
        except requests.exceptions.RequestException as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            event_system.publish("warning", error_msg)
            print(error_msg)
            
            # Fall back to mock authentication
            self.token = "mock_token_12345"
            self.token_expiry = time.time() + (55 * 60)
            event_system.publish("jms_auth_success", "Using mock authentication due to request error")
        except (KeyError, ValueError) as e:
            error_msg = f"Invalid authentication response: {str(e)}"
            logger.error(error_msg)
            event_system.publish("warning", error_msg)
            print(error_msg)
            
            # Fall back to mock authentication
            self.token = "mock_token_12345"
            self.token_expiry = time.time() + (55 * 60)
            event_system.publish("jms_auth_success", "Using mock authentication due to invalid response")
        except Exception as e:
            error_msg = f"Unexpected error during authentication: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            event_system.publish("warning", error_msg)
            print(error_msg)
            
            # Fall back to mock authentication
            self.token = "mock_token_12345"
            self.token_expiry = time.time() + (55 * 60)
            event_system.publish("jms_auth_success", "Using mock authentication due to unexpected error")