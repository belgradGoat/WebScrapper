"""
Results Tab Module for NC Tool Analyzer
Provides the results tab as a module
"""
import logging
from typing import List, Any

from module_system.module_interface import TabModuleInterface
from ui.results_tab import ResultsTab

logger = logging.getLogger(__name__)


class ResultsTabModule(TabModuleInterface):
    """Module that provides the results tab"""
    
    def __init__(self):
        """Initialize the module"""
        self.results_tab = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "results_tab_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the results tab for viewing analysis results"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["analysis_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing results tab module")
        
        # Get the required services
        self.analysis_service = service_registry.get_service("analysis_service")
        if not self.analysis_service:
            raise ValueError("Analysis service not found")
    
    def get_tab(self, parent) -> Any:
        """Return the tab frame for this module"""
        logger.info("Creating results tab")
        self.results_tab = ResultsTab(parent, self.analysis_service)
        return self.results_tab.frame
    
    def get_tab_name(self) -> str:
        """Return the name of the tab"""
        return "Results"
    
    def get_tab_icon(self) -> str:
        """Return the icon for the tab"""
        return "📊"
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down results tab module")
        # No specific shutdown needed for results tab