"""
JMS Menu Extension Module for NC Tool Analyzer
Provides menu extensions for JMS configuration
"""
import logging
import tkinter as tk
from typing import Dict, List, Any

from module_system.module_interface import ModuleInterface
from utils.event_system import event_system

logger = logging.getLogger(__name__)

# Try to import JMS config dialog
try:
    logger.info("Attempting to import JMS config dialog...")
    # Try absolute imports first
    try:
        from ui.jms_config_dialog import JMSConfigDialog
        logger.info("Successfully imported JMSConfigDialog using absolute import")
        JMS_CONFIG_AVAILABLE = True
    except ImportError:
        # Try relative imports
        logger.info("Absolute imports failed, trying relative imports...")
        import sys
        import os
        # Add parent directory to path to enable relative imports
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
            logger.info(f"Added parent directory to path: {parent_dir}")
        
        from ui.jms_config_dialog import JMSConfigDialog
        logger.info("Successfully imported JMSConfigDialog using relative import")
        JMS_CONFIG_AVAILABLE = True
except ImportError as e:
    JMS_CONFIG_AVAILABLE = False
    logger.error(f"JMS config dialog import error: {str(e)}")
    logger.error(f"Python path: {sys.path}")
    logger.warning("JMS config dialog not found. JMS configuration menu will not be available.")


class JMSMenuExtensionModule(ModuleInterface):
    """Module that provides JMS menu extensions"""
    
    def __init__(self):
        """Initialize the module"""
        self.jms_service = None
        self.main_window = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "jms_menu_extension_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides menu extensions for JMS configuration"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["jms_service_module", "extension_registry"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing JMS menu extension module")
        
        # Get the JMS service module
        logger.info("Looking for jms_service_module in service registry")
        self.jms_service_module = service_registry.get_service("jms_service_module")
        if not self.jms_service_module:
            logger.error("JMS service module not found in service registry")
            logger.error("Available services: " + ", ".join(service_registry._services.keys()))
            return
        else:
            logger.info(f"Found jms_service_module: {type(self.jms_service_module).__name__}")
            
        # Get the JMS service from the module
        logger.info("Looking for jms_service in service registry")
        self.jms_service = service_registry.get_service("jms_service")
        if not self.jms_service:
            logger.warning("JMS service not found. Using JMS service module directly.")
            self.jms_service = self.jms_service_module
        else:
            logger.info(f"Found jms_service: {type(self.jms_service).__name__}")
            
        # Get the extension registry
        logger.info("Looking for extension_registry in service registry")
        extension_registry = service_registry.get_service("extension_registry")
        if not extension_registry:
            logger.error("Extension registry not found. JMS menu extensions will not be available.")
            return
        else:
            logger.info("Found extension_registry")
            
        # Register menu extensions
        logger.info("Getting ui.menu.tools extension point")
        tools_menu_ext = extension_registry.get_extension_point("ui.menu.tools")
        logger.info("Registering handler for ui.menu.tools extension point")
        tools_menu_ext.register_handler(self._add_tools_menu_items)
        logger.info("Handler registered successfully")
    
    def _add_tools_menu_items(self, menu):
        """
        Add JMS configuration menu items to the tools menu
        
        Args:
            menu: Tools menu
        """
        logger.info("Adding JMS menu items to tools menu")
        if JMS_CONFIG_AVAILABLE:
            logger.info("JMS config dialog is available, adding menu item")
            menu.add_command(label="JMS Configuration...", command=self._open_jms_config)
            logger.info("JMS Configuration menu item added")
        else:
            logger.warning("JMS config dialog is not available, skipping menu item")
    
    def _open_jms_config(self):
        """Open the JMS configuration dialog"""
        logger.info("Opening JMS configuration dialog")
        if not JMS_CONFIG_AVAILABLE:
            logger.error("JMS configuration dialog is not available")
            tk.messagebox.showerror("Error", "JMS configuration is not available")
            return
            
        # Get the root window
        root = tk._default_root
        logger.info(f"Using root window: {root}")
        
        # Create the dialog with the JMS service module
        logger.info(f"Creating JMS config dialog with service: {type(self.jms_service).__name__}")
        JMSConfigDialog(root, self.jms_service)
        logger.info("JMS config dialog created")
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down JMS menu extension module")
        # No specific shutdown needed