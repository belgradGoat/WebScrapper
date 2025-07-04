"""
Module Interface for NC Tool Analyzer
Defines the base interfaces that all modules must implement
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class ModuleInterface(ABC):
    """Base interface that all modules must implement"""
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the name of the module"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Return the version of the module"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a description of the module"""
        pass
    
    @abstractmethod
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        pass
    
    @abstractmethod
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        pass
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        pass


class TabModuleInterface(ModuleInterface):
    """Interface for modules that provide UI tabs"""
    
    @abstractmethod
    def get_tab(self, parent) -> Any:
        """Return the tab frame for this module"""
        pass
    
    @abstractmethod
    def get_tab_name(self) -> str:
        """Return the name of the tab"""
        pass
    
    def get_tab_icon(self) -> Optional[str]:
        """Return the icon for the tab (emoji or None)"""
        return None


class ServiceModuleInterface(ModuleInterface):
    """Interface for modules that provide services"""
    
    @abstractmethod
    def get_provided_services(self) -> Dict[str, Any]:
        """Return a dictionary of services provided by this module"""
        pass