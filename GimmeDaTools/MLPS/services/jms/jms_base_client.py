"""
Base client for JMS API interactions
"""
import json
from typing import Dict, Any, Optional, List, Union, TypeVar
from utils.event_system import event_system
from .jms_auth import JMSAuthClient, REQUESTS_AVAILABLE

# Define a generic Response type to avoid direct reference to requests.Response
Response = TypeVar('Response')

# Create a mock Response class for when requests is not available
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

# Create a mock requests module
class MockRequests:
    @staticmethod
    def request(method, url, **kwargs):
        print(f"Mock {method} request to {url}")
        return MockResponse(200, {"status": "success", "message": "This is a mock response"})

# Import requests if available
if REQUESTS_AVAILABLE:
    try:
        import requests
        Response = requests.Response
        print("Using real requests module in JMS base client")
    except ImportError:
        # Fall back to mock requests
        print("Failed to import requests in JMS base client, using mock implementation")
        requests = MockRequests
        Response = MockResponse
else:
    # Use mock requests
    print("REQUESTS_AVAILABLE is False, using mock implementation in JMS base client")
    requests = MockRequests
    Response = MockResponse


class JMSBaseClient:
    """Base client for JMS API interactions"""
    
    def __init__(self, base_url: str, auth_client: Optional[JMSAuthClient] = None):
        """
        Initialize the JMS base client
        
        Args:
            base_url: Base URL of the JMS API
            auth_client: JMSAuthClient instance (created if not provided)
        """
        self.base_url = base_url
        self.api_base = f"{base_url}/esbusci"
        self.auth_client = auth_client or JMSAuthClient(base_url)
        
    def _ensure_authenticated(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Ensure request has authentication headers
        
        Args:
            headers: Existing headers to augment with authentication
            
        Returns:
            Headers dictionary with authentication
        """
        headers = headers or {}
        auth_header = self.auth_client.get_auth_header()
        return {**headers, **auth_header}
    
    def _make_request(self, method: str, endpoint: str,
                     data: Optional[Dict[str, Any]] = None,
                     params: Optional[Dict[str, Any]] = None,
                     headers: Optional[Dict[str, str]] = None) -> Any:
        """
        Make an authenticated request to the JMS API
        
        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (relative to api_base)
            data: Request body data
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response object
            
        Raises:
            Exception: If request fails after retry
        """
        # Check if we should use mock implementation
        if not REQUESTS_AVAILABLE or not hasattr(requests, 'request'):
            print(f"Using mock implementation for {method} request to {endpoint}")
            return MockResponse(200, {"status": "success", "message": "This is a mock response"})
            
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = self._ensure_authenticated(headers)
        
        if headers.get("Content-Type") is None:
            headers["Content-Type"] = "application/json"
            
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers
            )
            
            # Handle 401 by refreshing token and retrying once
            if response.status_code == 401:
                # Token might be expired, refresh and retry once
                self.auth_client._refresh_token()
                headers = self._ensure_authenticated(headers)
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
            return response
        except Exception as e:
            error_msg = f"Request failed: {method} {url} - {str(e)}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request
        
        Args:
            endpoint: API endpoint (relative to api_base)
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails
        """
        response = self._make_request("GET", endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"GET request failed: {response.status_code} - {response.text}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a POST request
        
        Args:
            endpoint: API endpoint (relative to api_base)
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails
        """
        response = self._make_request("POST", endpoint, data=data)
        if response.status_code in (200, 201):
            return response.json()
        else:
            error_msg = f"POST request failed: {response.status_code} - {response.text}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PUT request
        
        Args:
            endpoint: API endpoint (relative to api_base)
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails
        """
        response = self._make_request("PUT", endpoint, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"PUT request failed: {response.status_code} - {response.text}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a PATCH request
        
        Args:
            endpoint: API endpoint (relative to api_base)
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            Exception: If request fails
        """
        response = self._make_request("PATCH", endpoint, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"PATCH request failed: {response.status_code} - {response.text}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)
    
    def delete(self, endpoint: str) -> bool:
        """
        Make a DELETE request
        
        Args:
            endpoint: API endpoint (relative to api_base)
            
        Returns:
            True if successful
            
        Raises:
            Exception: If request fails
        """
        response = self._make_request("DELETE", endpoint)
        if response.status_code in (200, 204):
            return True
        else:
            error_msg = f"DELETE request failed: {response.status_code} - {response.text}"
            event_system.publish("error", error_msg)
            raise Exception(error_msg)