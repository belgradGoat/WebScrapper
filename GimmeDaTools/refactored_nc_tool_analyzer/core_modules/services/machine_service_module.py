"""
Machine Service Module for NC Tool Analyzer
Provides the machine service as a module
"""
import logging
from typing import Dict, List, Any

from module_system.module_interface import ServiceModuleInterface
from services.machine_service import MachineService

logger = logging.getLogger(__name__)


class MachineServiceModule(ServiceModuleInterface):
    """Module that provides the machine service"""
    
    def __init__(self):
        """Initialize the module"""
        self.machine_service = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "machine_service_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the machine service for managing machines and their tools"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return []
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing machine service module")
        self.machine_service = MachineService()
    
    def get_provided_services(self) -> Dict[str, Any]:
        """Return a dictionary of services provided by this module"""
        return {
            "machine_service": self.machine_service
        }
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down machine service module")
        # No specific shutdown needed for machine service