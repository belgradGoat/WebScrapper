"""
Analysis Service Module for NC Tool Analyzer
Provides the analysis service as a module
"""
import logging
from typing import Dict, List, Any

from module_system.module_interface import ServiceModuleInterface
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class AnalysisServiceModule(ServiceModuleInterface):
    """Module that provides the analysis service"""
    
    def __init__(self):
        """Initialize the module"""
        self.analysis_service = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "analysis_service_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the analysis service for analyzing NC files"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["machine_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing analysis service module")
        
        # Get the machine service
        machine_service = service_registry.get_service("machine_service")
        if not machine_service:
            raise ValueError("Machine service not found")
        
        # Create the analysis service
        self.analysis_service = AnalysisService(machine_service)
    
    def get_provided_services(self) -> Dict[str, Any]:
        """Return a dictionary of services provided by this module"""
        return {
            "analysis_service": self.analysis_service
        }
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down analysis service module")
        # No specific shutdown needed for analysis service