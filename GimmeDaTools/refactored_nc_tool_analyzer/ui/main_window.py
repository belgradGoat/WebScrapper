"""
Main Window for NC Tool Analyzer
Uses the module system for dynamic tab loading and service access
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Any

from module_system.module_interface import TabModuleInterface
from utils.event_system import event_system

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Main window for the NC Tool Analyzer application
    """
    def __init__(self, root, app_core):
        """
        Initialize the main window
        
        Args:
            root: Tkinter root window
            app_core: ApplicationCore instance
        """
        self.root = root
        self.root.title("NC Tool Analyzer")
        self.root.geometry("1200x800")
        
        # Store application core
        self.app_core = app_core
        
        # Get service registry
        self.service_registry = app_core.get_service_registry()
        
        # Get extension registry
        self.extension_registry = app_core.get_extension_registry()
        
        # Setup UI
        self.setup_ui()
        
        # Create menu
        self._create_menu()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def setup_ui(self):
        """Set up the main UI components"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load core tabs
        self._load_core_tabs()
        
        # Load module tabs
        self._load_module_tabs()
    
    def _load_core_tabs(self):
        """Load core tabs from the core modules"""
        logger.info("Loading core tabs")
        
        # Get the module registry
        module_registry = self.app_core.get_module_registry()
        
        # Get all tab modules from core_modules
        tab_modules = module_registry.get_modules_by_type(TabModuleInterface)
        
        if not tab_modules:
            logger.warning("No core tab modules found")
            
        # Add each tab to the notebook
        for module in tab_modules:
            try:
                logger.info(f"Loading tab from module: {module.get_name()}")
                tab = module.get_tab(self.notebook)
                tab_name = module.get_tab_name()
                tab_icon = module.get_tab_icon() or ""
                
                # Add the tab to the notebook
                self.notebook.add(tab, text=f"{tab_icon} {tab_name}")
                
            except Exception as e:
                logger.error(f"Error loading tab from module {module.get_name()}: {str(e)}")
    
    def _load_module_tabs(self):
        """Load tabs from user modules"""
        # This will be implemented when user modules are supported
        pass
        
    def _setup_event_handlers(self):
        """Set up event handlers for application events"""
        # Switch to results tab when analysis is complete
        event_system.subscribe("analysis_complete", self._on_analysis_complete)
        
        # Handle errors
        event_system.subscribe("error", self._on_error)
        
        # Handle JMS events
        event_system.subscribe("jms_auth_success", self._on_jms_event)
        event_system.subscribe("jms_polling_started", self._on_jms_event)
        event_system.subscribe("jms_polling_stopped", self._on_jms_event)
        
    def _on_analysis_complete(self, analysis_result):
        """
        Handle analysis complete event
        
        Args:
            analysis_result: AnalysisResult object
        """
        # Stay on analysis tab to see summary
        # User can switch to Results tab for detailed info
        pass
        
    def _on_error(self, error_message):
        """
        Handle error event
        
        Args:
            error_message: Error message to display
        """
        tk.messagebox.showerror("Error", error_message)
    
    def _on_jms_event(self, message):
        """
        Handle JMS event
        
        Args:
            message: Event message
        """
        # Log JMS events to console for now
        print(f"JMS Event: {message}")
        
    def _create_menu(self):
        """Create the application menu"""
        logger.info("Creating application menu")
        
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        logger.info("Creating File menu")
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Add file menu items from extension points
        logger.info("Getting ui.menu.file extension point")
        file_ext_point = self.extension_registry.get_extension_point("ui.menu.file")
        logger.info("Invoking ui.menu.file extension point")
        file_ext_point.invoke(file_menu)
        
        # Add exit command
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        logger.info("Creating Tools menu")
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Add Settings menu item
        logger.info("Adding Settings menu item")
        tools_menu.add_command(label="Settings...", command=self._show_settings)
        
        # Add JMS Configuration menu item directly
        logger.info("Checking for JMS service")
        jms_service = self.service_registry.get_service("jms_service")
        if jms_service:
            logger.info("JMS service found, adding JMS Configuration menu item")
            tools_menu.add_command(label="JMS Configuration...", command=self._show_jms_config)
        else:
            logger.warning("JMS service not found, skipping JMS Configuration menu item")
            # Check if JMS service module is available
            jms_service_module = self.service_registry.get_service("jms_service_module")
            if jms_service_module:
                logger.info("JMS service module found, adding JMS Configuration menu item")
                tools_menu.add_command(label="JMS Configuration...", command=self._show_jms_config)
        
        # Add tools menu items from extension points
        logger.info("Getting ui.menu.tools extension point")
        tools_ext_point = self.extension_registry.get_extension_point("ui.menu.tools")
        logger.info("Invoking ui.menu.tools extension point")
        tools_ext_point.invoke(tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        # Add help menu items from extension points
        help_ext_point = self.extension_registry.get_extension_point("ui.menu.help")
        help_ext_point.invoke(help_menu)
        
        # Add about command
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)
    
    def _show_about(self):
        """Show the about dialog"""
        # Get version from config
        version = self.app_core.get_config_manager().get_value("app.version", "1.0.0")
        
        messagebox.showinfo(
            "About NC Tool Analyzer",
            "NC Tool Analyzer\n\n"
            "A tool for analyzing NC programs and scheduling machine shop operations.\n\n"
            f"Version {version}"
        )
        
    def _show_settings(self):
        """Show the settings dialog"""
        from ui.settings_dialog import SettingsDialog
        try:
            SettingsDialog(self.root, self.app_core)
        except ImportError:
            messagebox.showinfo(
                "Settings",
                "Settings dialog not implemented yet."
            )
    
    def _show_jms_config(self):
        """Show the JMS configuration dialog"""
        logger.info("Showing JMS configuration dialog")
        try:
            logger.info("Importing JMSConfigDialog")
            from ui.jms_config_dialog import JMSConfigDialog
            
            logger.info("Getting JMS service")
            jms_service = self.service_registry.get_service("jms_service")
            if jms_service:
                logger.info(f"Using JMS service: {type(jms_service).__name__}")
                JMSConfigDialog(self.root, jms_service)
            else:
                logger.warning("JMS service not found, trying JMS service module")
                jms_service_module = self.service_registry.get_service("jms_service_module")
                if jms_service_module:
                    logger.info(f"Using JMS service module: {type(jms_service_module).__name__}")
                    JMSConfigDialog(self.root, jms_service_module)
                else:
                    logger.error("Neither JMS service nor JMS service module found")
                    messagebox.showerror("Error", "JMS service not available")
        except ImportError as e:
            logger.error(f"Error importing JMS configuration dialog: {str(e)}")
            messagebox.showerror("Error", "JMS configuration dialog not available")
        except Exception as e:
            logger.error(f"Error showing JMS configuration dialog: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error showing JMS configuration: {str(e)}")
    
    def get_service(self, name):
        """
        Get a service by name
        
        Args:
            name: Name of the service
            
        Returns:
            Service instance or None if not found
        """
        return self.service_registry.get_service(name)