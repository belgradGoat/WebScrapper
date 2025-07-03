"""
Scheduler Tab Module for NC Tool Analyzer
Provides the scheduler tab as a module
"""
import logging
from typing import List, Any

from module_system.module_interface import TabModuleInterface
from ui.scheduler_tab import SchedulerTab

logger = logging.getLogger(__name__)


class SchedulerTabModule(TabModuleInterface):
    """Module that provides the scheduler tab"""
    
    def __init__(self):
        """Initialize the module"""
        self.scheduler_tab = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "scheduler_tab_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the scheduler tab for scheduling jobs and parts"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["scheduler_service", "machine_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing scheduler tab module")
        
        # Get the required services
        self.scheduler_service = service_registry.get_service("scheduler_service")
        if not self.scheduler_service:
            raise ValueError("Scheduler service not found")
            
        self.machine_service = service_registry.get_service("machine_service")
        if not self.machine_service:
            raise ValueError("Machine service not found")
        
        # Get optional JMS service
        self.jms_service = service_registry.get_service("jms_service")
    
    def get_tab(self, parent) -> Any:
        """Return the tab frame for this module"""
        logger.info("Creating scheduler tab")
        self.scheduler_tab = SchedulerTab(parent, self.scheduler_service, self.machine_service)
        
        # Set JMS service if available
        if self.jms_service:
            self.scheduler_tab.set_jms_service(self.jms_service)
            
        return self.scheduler_tab.frame
    
    def get_tab_name(self) -> str:
        """Return the name of the tab"""
        return "Scheduler"
    
    def get_tab_icon(self) -> str:
        """Return the icon for the tab"""
        return "📅"
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down scheduler tab module")
        # No specific shutdown needed for scheduler tab