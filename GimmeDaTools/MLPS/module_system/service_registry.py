"""
Service Registry for NC Tool Analyzer
Provides a registry for services that can be used by modules
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


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
        logger.info(f"Registering service: {name} ({type(service).__name__})")
        self.services[name] = service
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get a service by name
        
        Args:
            name: Name of the service
            
        Returns:
            Service instance or None if not found
        """
        service = self.services.get(name)
        if service:
            logger.info(f"Retrieved service: {name} ({type(service).__name__})")
        else:
            logger.warning(f"Service not found: {name}")
            logger.debug(f"Available services: {', '.join(self.services.keys())}")
        return service
    
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
        logger.info(f"Getting all services. {len(self.services)} services available")
        return self.services.copy()