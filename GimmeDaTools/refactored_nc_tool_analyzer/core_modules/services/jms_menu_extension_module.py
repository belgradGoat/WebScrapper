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
    from ui.jms_config_dialog import JMSConfigDialog
    JMS_CONFIG_AVAILABLE = True
except ImportError:
    JMS_CONFIG_AVAILABLE = False
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
        return ["jms_service", "extension_registry"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing JMS menu extension module")
        
        # Get the JMS service
        self.jms_service = service_registry.get_service("jms_service")
        if not self.jms_service:
            logger.warning("JMS service not found. JMS menu extensions will not be available.")
            return
            
        # Get the extension registry
        extension_registry = service_registry.get_service("extension_registry")
        if not extension_registry:
            logger.warning("Extension registry not found. JMS menu extensions will not be available.")
            return
            
        # Register menu extensions
        tools_menu_ext = extension_registry.get_extension_point("ui.menu.tools")
        tools_menu_ext.register_handler(self._add_tools_menu_items)
    
    def _add_tools_menu_items(self, menu):
        """
        Add JMS configuration menu items to the tools menu
        
        Args:
            menu: Tools menu
        """
        if JMS_CONFIG_AVAILABLE:
            menu.add_command(label="JMS Configuration", command=self._open_jms_config)
    
    def _open_jms_config(self):
        """Open the JMS configuration dialog"""
        if not JMS_CONFIG_AVAILABLE:
            tk.messagebox.showerror("Error", "JMS configuration is not available")
            return
            
        # Get the main window from the application
        if not self.main_window:
            # Try to find the main window
            for widget in tk._default_root.winfo_children():
                if widget.winfo_class() == "Tk":
                    self.main_window = widget
                    break
        
        if self.main_window:
            JMSConfigDialog(self.main_window, self.jms_service)
        else:
            JMSConfigDialog(tk._default_root, self.jms_service)
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down JMS menu extension module")
        # No specific shutdown needed