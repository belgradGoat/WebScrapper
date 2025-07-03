"""
Factory for JMS API clients
"""
from typing import Optional
from .jms_auth import JMSAuthClient
from .jms_cell_client import JMSCellClient
from .jms_order_client import JMSOrderClient
from .jms_production_client import JMSProductionClient
from .jms_mdc_client import JMSMDCClient


class JMSClient:
    """Factory for JMS API clients"""
    
    def __init__(self, base_url: str, client_id: str = "EsbusciClient", 
                 client_secret: str = "DefaultEsbusciClientSecret"):
        """
        Initialize the JMS client factory
        
        Args:
            base_url: Base URL of the JMS API
            client_id: OAuth2 client ID (default: EsbusciClient)
            client_secret: OAuth2 client secret (default: DefaultEsbusciClientSecret)
        """
        self.base_url = base_url
        self.auth_client = JMSAuthClient(base_url, client_id, client_secret)
        
        # Initialize client instances
        self._cell = None
        self._order = None
        self._production = None
        self._mdc = None
    
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
            # Try to get an authentication token
            self.auth_client.get_auth_header()
            return True
        except Exception:
            return False