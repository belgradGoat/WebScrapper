"""
Scheduler Service Module for NC Tool Analyzer
Provides the scheduler service as a module
"""
import logging
from typing import Dict, List, Any

from module_system.module_interface import ServiceModuleInterface
from services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)


class SchedulerServiceModule(ServiceModuleInterface):
    """Module that provides the scheduler service"""
    
    def __init__(self):
        """Initialize the module"""
        self.scheduler_service = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "scheduler_service_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the scheduler service for scheduling jobs and parts"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["machine_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing scheduler service module")
        
        # Get the machine service
        machine_service = service_registry.get_service("machine_service")
        if not machine_service:
            raise ValueError("Machine service not found")
        
        # Create the scheduler service
        self.scheduler_service = SchedulerService(machine_service)
    
    def get_provided_services(self) -> Dict[str, Any]:
        """Return a dictionary of services provided by this module"""
        return {
            "scheduler_service": self.scheduler_service
        }
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down scheduler service module")
        # No specific shutdown needed for scheduler service