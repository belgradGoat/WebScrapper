"""
Service Registry for NC Tool Analyzer
Provides a registry for services that can be used by modules
"""
from typing import Dict, Any, Optional


class ServiceRegistry:
    """Registry for core and module-provided services"""
    
    def __init__(self):
        """Initialize the service registry"""
        self.services = {}
    
    def register_service(self, name: str, service: Any) -> None:
        """
        Register a service with the registry
        
        Args:
            name: Name of the service
            service: Service instance
        """
        self.services[name] = service
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get a service by name
        
        Args:
            name: Name of the service
            
        Returns:
            Service instance or None if not found
        """
        return self.services.get(name)
    
    def has_service(self, name: str) -> bool:
        """
        Check if a service exists
        
        Args:
            name: Name of the service
            
        Returns:
            True if the service exists, False otherwise
        """
        return name in self.services
    
    def get_all_services(self) -> Dict[str, Any]:
        """
        Get all registered services
        
        Returns:
            Dictionary of all registered services
        """
        return self.services.copy()