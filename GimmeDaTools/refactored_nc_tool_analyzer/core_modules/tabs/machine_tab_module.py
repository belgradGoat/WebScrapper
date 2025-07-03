"""
Machine Tab Module for NC Tool Analyzer
Provides the machine tab as a module
"""
import logging
from typing import List, Any

from module_system.module_interface import TabModuleInterface
from ui.machine_tab import MachineTab

logger = logging.getLogger(__name__)


class MachineTabModule(TabModuleInterface):
    """Module that provides the machine tab"""
    
    def __init__(self):
        """Initialize the module"""
        self.machine_tab = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "machine_tab_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the machine tab for managing machines"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["machine_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing machine tab module")
        
        # Get the required services
        self.machine_service = service_registry.get_service("machine_service")
        if not self.machine_service:
            raise ValueError("Machine service not found")
    
    def get_tab(self, parent) -> Any:
        """Return the tab frame for this module"""
        logger.info("Creating machine tab")
        self.machine_tab = MachineTab(parent, self.machine_service)
        return self.machine_tab.frame
    
    def get_tab_name(self) -> str:
        """Return the name of the tab"""
        return "Machine Management"
    
    def get_tab_icon(self) -> str:
        """Return the icon for the tab"""
        return "🏭"
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down machine tab module")
        # No specific shutdown needed for machine tab