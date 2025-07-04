"""
Application Core for NC Tool Analyzer
Manages the module system and provides access to core services
"""
import os
import logging
from typing import Optional

from module_system.service_registry import ServiceRegistry
from module_system.module_registry import ModuleRegistry
from module_system.config_manager import ConfigManager
from module_system.extension_registry import ExtensionRegistry

logger = logging.getLogger(__name__)


class ApplicationCore:
    """Core application class that manages the module system"""
    
    def __init__(self):
        """Initialize the application core"""
        self.service_registry = ServiceRegistry()
        self.module_registry = ModuleRegistry()
        self.config_manager = ConfigManager()
        self.extension_registry = ExtensionRegistry()
        
        # Register core paths
        self._register_core_paths()
        
        # Register the core services
        self._register_core_services()
        
        # Register core extension points
        self._register_core_extension_points()
    
    def _register_core_paths(self):
        """Register core module paths"""
        # Get the base directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Register core modules path
        core_modules_path = os.path.join(base_dir, "core_modules")
        if os.path.isdir(core_modules_path):
            self.module_registry.add_module_path(core_modules_path)
        
        # Register user modules path
        user_modules_path = os.path.join(base_dir, "modules")
        if os.path.isdir(user_modules_path):
            self.module_registry.add_module_path(user_modules_path)
        else:
            # Create the directory if it doesn't exist
            os.makedirs(user_modules_path, exist_ok=True)
            self.module_registry.add_module_path(user_modules_path)
    
    def _register_core_services(self):
        """Register core services"""
        # Register the core components as services
        self.service_registry.register_service("service_registry", self.service_registry)
        self.service_registry.register_service("module_registry", self.module_registry)
        self.service_registry.register_service("config_manager", self.config_manager)
        self.service_registry.register_service("extension_registry", self.extension_registry)
        self.service_registry.register_service("app_core", self)
    
    def _register_core_extension_points(self):
        """Register core extension points"""
        # Application lifecycle extension points
        self.extension_registry.register_extension_point("app.startup")
        self.extension_registry.register_extension_point("app.shutdown")
        
        # UI extension points
        self.extension_registry.register_extension_point("ui.menu.file")
        self.extension_registry.register_extension_point("ui.menu.tools")
        self.extension_registry.register_extension_point("ui.menu.help")
        self.extension_registry.register_extension_point("ui.toolbar")
        self.extension_registry.register_extension_point("ui.statusbar")
    
    def initialize(self):
        """Initialize the application core and all modules"""
        try:
            # Discover modules
            logger.info("Discovering modules...")
            self.module_registry.discover_modules()
            
            # Initialize modules
            logger.info("Initializing modules...")
            self.module_registry.initialize_modules(self.service_registry)
            
            # Invoke startup extension point
            logger.info("Invoking startup extensions...")
            startup_point = self.extension_registry.get_extension_point("app.startup")
            startup_point.invoke(self)
            
            logger.info("Application core initialized successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing application core: {str(e)}")
            return False
    
    def shutdown(self):
        """Shutdown the application core and all modules"""
        try:
            # Invoke shutdown extension point
            logger.info("Invoking shutdown extensions...")
            shutdown_point = self.extension_registry.get_extension_point("app.shutdown")
            shutdown_point.invoke(self)
            
            # Shutdown modules
            logger.info("Shutting down modules...")
            self.module_registry.shutdown_modules()
            
            logger.info("Application core shut down successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error shutting down application core: {str(e)}")
            return False
    
    def get_service_registry(self) -> ServiceRegistry:
        """Get the service registry"""
        return self.service_registry
    
    def get_module_registry(self) -> ModuleRegistry:
        """Get the module registry"""
        return self.module_registry
    
    def get_config_manager(self) -> ConfigManager:
        """Get the configuration manager"""
        return self.config_manager
    
    def get_extension_registry(self) -> ExtensionRegistry:
        """Get the extension registry"""
        return self.extension_registry