"""
Analysis Tab Module for NC Tool Analyzer
Provides the analysis tab as a module
"""
import logging
from typing import List, Any

from module_system.module_interface import TabModuleInterface
from ui.analysis_tab import AnalysisTab

logger = logging.getLogger(__name__)


class AnalysisTabModule(TabModuleInterface):
    """Module that provides the analysis tab"""
    
    def __init__(self):
        """Initialize the module"""
        self.analysis_tab = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "analysis_tab_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the analysis tab for analyzing NC files"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["analysis_service", "machine_service", "scheduler_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing analysis tab module")
        
        # Get the required services
        self.analysis_service = service_registry.get_service("analysis_service")
        if not self.analysis_service:
            raise ValueError("Analysis service not found")
            
        self.machine_service = service_registry.get_service("machine_service")
        if not self.machine_service:
            raise ValueError("Machine service not found")
            
        self.scheduler_service = service_registry.get_service("scheduler_service")
        if not self.scheduler_service:
            raise ValueError("Scheduler service not found")
    
    def get_tab(self, parent) -> Any:
        """Return the tab frame for this module"""
        logger.info("Creating analysis tab")
        self.analysis_tab = AnalysisTab(parent, self.analysis_service, self.machine_service, self.scheduler_service)
        return self.analysis_tab.frame
    
    def get_tab_name(self) -> str:
        """Return the name of the tab"""
        return "Analysis"
    
    def get_tab_icon(self) -> str:
        """Return the icon for the tab"""
        return "🔍"
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down analysis tab module")
        # No specific shutdown needed for analysis tab