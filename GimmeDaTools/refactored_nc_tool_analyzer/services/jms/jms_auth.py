"""
JMS Authentication Client for OAuth2 authentication with JMS API
"""
import requests
import time
from typing import Dict, Optional
from utils.event_system import event_system


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