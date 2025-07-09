"""
Factory for JMS API clients
"""
from typing import Optional
from .jms_auth import JMSAuthClient
from .jms_cell_client import JMSCellClient
from .jms_order_client import JMSOrderClient
from .jms_production_client import JMSProductionClient
from .jms_mdc_client import JMSMDCClient


# Import REQUESTS_AVAILABLE flag
from .jms_auth import REQUESTS_AVAILABLE

class JMSClient:
    """Factory for JMS API clients"""
    
    def __init__(self, base_url: str, client_id: str = "EsbusciClient",
                 client_secret: str = "DefaultEsbusciClientSecret",
                 username: str = None, password: str = None):
        """
        Initialize the JMS client factory
        
        Args:
            base_url: Base URL of the JMS API
            client_id: OAuth2 client ID (default: EsbusciClient)
            client_secret: OAuth2 client secret (default: DefaultEsbusciClientSecret)
            username: Username for authentication (optional)
            password: Password for authentication (optional)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"=== JMS CLIENT INITIALIZATION ===")
        logger.info(f"JMSClient instance ID: {id(self)}")
        logger.info(f"Constructor parameter base_url: {base_url}")
        logger.info(f"Constructor parameter client_id: {client_id}")
        logger.info(f"Constructor parameter username: {username}")
        
        self.base_url = base_url
        logger.info(f"self.base_url set to: {self.base_url}")
        
        logger.info(f"Creating JMSAuthClient with base_url: {base_url}")
        self.auth_client = JMSAuthClient(base_url, client_id, client_secret, username, password)
        logger.info(f"JMSAuthClient created with ID: {id(self.auth_client)}")
        logger.info(f"JMSAuthClient base_url: {self.auth_client.base_url}")
        
        # Initialize client instances
        self._cell = None
        self._order = None
        self._production = None
        self._mdc = None
        
        # Print status
        if REQUESTS_AVAILABLE:
            print(f"JMSClient initialized with real HTTP client, base URL: {base_url}")
            logger.info(f"JMSClient initialized with real HTTP client, base URL: {base_url}")
        else:
            print(f"JMSClient initialized with mock HTTP client, base URL: {base_url}")
            logger.info(f"JMSClient initialized with mock HTTP client, base URL: {base_url}")
        
        logger.info(f"=== JMS CLIENT INITIALIZATION COMPLETE ===")
        logger.info(f"Final JMSClient base_url: {self.base_url}")
        logger.info(f"Final JMSAuthClient base_url: {self.auth_client.base_url}")
        
    @property
    def cell(self) -> JMSCellClient:
        """
        Get the JMS Cell client
        
        Returns:
            JMSCellClient instance
        """
        if not self._cell:
            self._cell = JMSCellClient(self.base_url, self.auth_client)
        return self._cell
    
    @property
    def order(self) -> JMSOrderClient:
        """
        Get the JMS Order client
        
        Returns:
            JMSOrderClient instance
        """
        if not self._order:
            self._order = JMSOrderClient(self.base_url, self.auth_client)
        return self._order
    
    @property
    def production(self) -> JMSProductionClient:
        """
        Get the JMS Production client
        
        Returns:
            JMSProductionClient instance
        """
        if not self._production:
            self._production = JMSProductionClient(self.base_url, self.auth_client)
        return self._production
    
    @property
    def mdc(self) -> JMSMDCClient:
        """
        Get the JMS Machine Data Collection client
        
        Returns:
            JMSMDCClient instance
        """
        if not self._mdc:
            self._mdc = JMSMDCClient(self.base_url, self.auth_client)
        return self._mdc
    
    def test_connection(self) -> bool:
        """
        Test the connection to the JMS API
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # If using mock client, always return True
            if not REQUESTS_AVAILABLE:
                print("Using mock connection test, returning True")
                return True
                
            # Try to get an authentication token
            print("Testing connection by requesting auth header")
            self.auth_client.get_auth_header()
            print("Connection test successful")
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False