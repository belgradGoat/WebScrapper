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
        # Initialize tab management data structures
        self.tab_modules = {}  # Maps module_name -> module info
        self.tab_widgets = {}  # Maps module_name -> tab widget
        self.default_tab_order = []  # Default tab order for reset
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bind right-click event for context menu
        self.notebook.bind("<Button-3>", self._show_tab_context_menu)
        
        # Load core tabs
        self._load_core_tabs()
        
        # Load module tabs
        self._load_module_tabs()
        
        # Apply saved tab configuration
        self._apply_saved_tab_config()
    
    def _load_core_tabs(self):
        """Load core tabs from the core modules"""
        logger.info("Loading core tabs")
        
        # Get the module registry
        module_registry = self.app_core.get_module_registry()
        
        # Get all tab modules from core_modules
        tab_modules = module_registry.get_modules_by_type(TabModuleInterface)
        
        if not tab_modules:
            logger.warning("No core tab modules found")
            
        # Add each tab to the notebook and store module info
        for module in tab_modules:
            try:
                logger.info(f"Loading tab from module: {module.get_name()}")
                tab_widget = module.get_tab(self.notebook)
                tab_name = module.get_tab_name()
                tab_icon = module.get_tab_icon() or ""
                module_name = module.get_name()
                
                # Store module information
                self.tab_modules[module_name] = {
                    'module': module,
                    'tab_name': tab_name,
                    'tab_icon': tab_icon,
                    'display_text': f"{tab_icon} {tab_name}",
                    'visible': True
                }
                
                # Store tab widget
                self.tab_widgets[module_name] = tab_widget
                
                # Add to default tab order
                self.default_tab_order.append(module_name)
                
                # Add the tab to the notebook (initially, we'll rearrange later)
                self.notebook.add(tab_widget, text=f"{tab_icon} {tab_name}")
                
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
    
    def _show_tab_context_menu(self, event):
        """
        Show context menu for tab management
        
        Args:
            event: Tkinter event object
        """
        try:
            # Find which tab was clicked
            clicked_tab_index = self.notebook.index(f"@{event.x},{event.y}")
            
            # Get the tab widget at this index
            tab_widget = self.notebook.nametowidget(self.notebook.tabs()[clicked_tab_index])
            
            # Find the module name for this tab widget
            clicked_module_name = None
            for module_name, widget in self.tab_widgets.items():
                if widget == tab_widget:
                    clicked_module_name = module_name
                    break
            
            if not clicked_module_name:
                return
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            
            # Tab movement options
            context_menu.add_command(label="Move Left",
                                   command=lambda: self._move_tab(clicked_module_name, "left"))
            context_menu.add_command(label="Move Right",
                                   command=lambda: self._move_tab(clicked_module_name, "right"))
            context_menu.add_separator()
            context_menu.add_command(label="Move to First",
                                   command=lambda: self._move_tab(clicked_module_name, "first"))
            context_menu.add_command(label="Move to Last",
                                   command=lambda: self._move_tab(clicked_module_name, "last"))
            context_menu.add_separator()
            
            # Hide/Show functionality
            context_menu.add_command(label="Hide Tab",
                                   command=lambda: self._hide_tab(clicked_module_name))
            
            # Show hidden tabs submenu if any are hidden
            hidden_tabs = [name for name, info in self.tab_modules.items() if not info['visible']]
            if hidden_tabs:
                show_menu = tk.Menu(context_menu, tearoff=0)
                for hidden_tab in hidden_tabs:
                    tab_info = self.tab_modules[hidden_tab]
                    show_menu.add_command(label=f"Show {tab_info['tab_name']}",
                                        command=lambda name=hidden_tab: self._show_tab(name))
                context_menu.add_cascade(label="Show Hidden Tab", menu=show_menu)
            
            context_menu.add_separator()
            context_menu.add_command(label="Reset to Default Order",
                                   command=self._reset_tab_order)
            
            # Show the context menu
            context_menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            logger.error(f"Error showing tab context menu: {str(e)}")
    
    def _move_tab(self, module_name, direction):
        """
        Move a tab in the specified direction
        
        Args:
            module_name: Name of the module whose tab to move
            direction: 'left', 'right', 'first', or 'last'
        """
        try:
            # Get current tab order (visible tabs only)
            current_order = self._get_current_tab_order()
            
            if module_name not in current_order:
                return
            
            current_index = current_order.index(module_name)
            new_index = current_index
            
            if direction == "left" and current_index > 0:
                new_index = current_index - 1
            elif direction == "right" and current_index < len(current_order) - 1:
                new_index = current_index + 1
            elif direction == "first":
                new_index = 0
            elif direction == "last":
                new_index = len(current_order) - 1
            
            if new_index != current_index:
                # Remove from current position and insert at new position
                current_order.pop(current_index)
                current_order.insert(new_index, module_name)
                
                # Rebuild notebook with new order
                self._rebuild_notebook_order(current_order)
                
                # Save configuration
                self._save_tab_config()
                
        except Exception as e:
            logger.error(f"Error moving tab: {str(e)}")
    
    def _hide_tab(self, module_name):
        """
        Hide a tab
        
        Args:
            module_name: Name of the module whose tab to hide
        """
        try:
            if module_name in self.tab_modules:
                self.tab_modules[module_name]['visible'] = False
                
                # Remove from notebook
                tab_widget = self.tab_widgets[module_name]
                self.notebook.forget(tab_widget)
                
                # Save configuration
                self._save_tab_config()
                
        except Exception as e:
            logger.error(f"Error hiding tab: {str(e)}")
    
    def _show_tab(self, module_name):
        """
        Show a hidden tab
        
        Args:
            module_name: Name of the module whose tab to show
        """
        try:
            if module_name in self.tab_modules:
                self.tab_modules[module_name]['visible'] = True
                
                # Rebuild notebook to add the tab back in proper position
                current_order = self._get_saved_tab_order()
                self._rebuild_notebook_order(current_order)
                
                # Save configuration
                self._save_tab_config()
                
        except Exception as e:
            logger.error(f"Error showing tab: {str(e)}")
    
    def _reset_tab_order(self):
        """Reset tabs to default order and show all tabs"""
        try:
            # Reset all tabs to visible
            for module_name in self.tab_modules:
                self.tab_modules[module_name]['visible'] = True
            
            # Rebuild with default order
            self._rebuild_notebook_order(self.default_tab_order)
            
            # Clear saved configuration
            config_manager = self.app_core.get_config_manager()
            config_manager.set_value("ui.tab_order", self.default_tab_order)
            config_manager.set_value("ui.hidden_tabs", [])
            config_manager.save_config()
            
            messagebox.showinfo("Tab Order Reset", "Tabs have been reset to default order and all hidden tabs are now visible.")
            
        except Exception as e:
            logger.error(f"Error resetting tab order: {str(e)}")
    
    def _get_current_tab_order(self):
        """
        Get the current order of visible tabs
        
        Returns:
            List of module names in current display order
        """
        current_order = []
        for i in range(self.notebook.index("end")):
            tab_widget = self.notebook.nametowidget(self.notebook.tabs()[i])
            for module_name, widget in self.tab_widgets.items():
                if widget == tab_widget and self.tab_modules[module_name]['visible']:
                    current_order.append(module_name)
                    break
        return current_order
    
    def _rebuild_notebook_order(self, desired_order):
        """
        Rebuild the notebook with the specified tab order
        
        Args:
            desired_order: List of module names in desired order
        """
        try:
            # Remove all tabs
            for tab in self.notebook.tabs():
                self.notebook.forget(tab)
            
            # Add tabs back in desired order (only visible ones)
            for module_name in desired_order:
                if (module_name in self.tab_modules and
                    module_name in self.tab_widgets and
                    self.tab_modules[module_name]['visible']):
                    
                    tab_widget = self.tab_widgets[module_name]
                    display_text = self.tab_modules[module_name]['display_text']
                    self.notebook.add(tab_widget, text=display_text)
            
        except Exception as e:
            logger.error(f"Error rebuilding notebook order: {str(e)}")
    
    def _save_tab_config(self):
        """Save current tab configuration to config file"""
        try:
            config_manager = self.app_core.get_config_manager()
            
            # Save tab order
            current_order = self._get_current_tab_order()
            config_manager.set_value("ui.tab_order", current_order)
            
            # Save hidden tabs
            hidden_tabs = [name for name, info in self.tab_modules.items() if not info['visible']]
            config_manager.set_value("ui.hidden_tabs", hidden_tabs)
            
            # Save to file
            config_manager.save_config()
            
        except Exception as e:
            logger.error(f"Error saving tab configuration: {str(e)}")
    
    def _get_saved_tab_order(self):
        """
        Get saved tab order from configuration
        
        Returns:
            List of module names in saved order, or default order if not found
        """
        try:
            config_manager = self.app_core.get_config_manager()
            saved_order = config_manager.get_value("ui.tab_order", self.default_tab_order)
            
            # Ensure all current modules are included (handle new modules)
            all_modules = set(self.tab_modules.keys())
            saved_modules = set(saved_order)
            
            # Add any new modules not in saved order to the end
            final_order = [m for m in saved_order if m in all_modules]
            for module in all_modules - saved_modules:
                final_order.append(module)
            
            return final_order
            
        except Exception as e:
            logger.error(f"Error getting saved tab order: {str(e)}")
            return self.default_tab_order
    
    def _apply_saved_tab_config(self):
        """Apply saved tab configuration (order and visibility)"""
        try:
            config_manager = self.app_core.get_config_manager()
            
            # Apply hidden tabs
            hidden_tabs = config_manager.get_value("ui.hidden_tabs", [])
            for module_name in hidden_tabs:
                if module_name in self.tab_modules:
                    self.tab_modules[module_name]['visible'] = False
            
            # Apply saved tab order
            saved_order = self._get_saved_tab_order()
            self._rebuild_notebook_order(saved_order)
            
        except Exception as e:
            logger.error(f"Error applying saved tab configuration: {str(e)}")

    def get_service(self, name):
        """
        Get a service by name
        
        Args:
            name: Name of the service
            
        Returns:
            Service instance or None if not found
        """
        return self.service_registry.get_service(name)