"""
Module System for NC Tool Analyzer
Provides a plugin-based architecture for extending the application
"""

from .module_interface import ModuleInterface, TabModuleInterface, ServiceModuleInterface
from .service_registry import ServiceRegistry
from .module_registry import ModuleRegistry
from .config_manager import ConfigManager
from .extension_registry import ExtensionRegistry

__all__ = [
    'ModuleInterface',
    'TabModuleInterface',
    'ServiceModuleInterface',
    'ServiceRegistry',
    'ModuleRegistry',
    'ConfigManager',
    'ExtensionRegistry'
]