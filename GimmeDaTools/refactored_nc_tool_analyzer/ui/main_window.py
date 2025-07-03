"""
Main Window for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk

from services.machine_service import MachineService
from services.analysis_service import AnalysisService
from services.scheduler_service import SchedulerService
from services.jms_service import JMSService
from ui.analysis_tab import AnalysisTab
from ui.machine_tab import MachineTab
from ui.results_tab import ResultsTab
from ui.scheduler_tab import SchedulerTab
from utils.event_system import event_system


from ui.jms_config_dialog import JMSConfigDialog


class MainWindow:
    """
    Main window for the NC Tool Analyzer application
    """
    def __init__(self, root):
        """
        Initialize the main window
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("NC Tool Analyzer")
        self.root.geometry("1200x800")
        
        # Initialize services
        self.machine_service = MachineService()
        self.analysis_service = AnalysisService(self.machine_service)
        self.scheduler_service = SchedulerService(self.machine_service)
        
        # Initialize JMS service (disabled by default)
        self.jms_service = JMSService(self.scheduler_service)
        self.jms_enabled = False
        
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
        
        # Create tabs
        self.analysis_tab = AnalysisTab(self.notebook, self.analysis_service, self.machine_service)
        self.machine_tab = MachineTab(self.notebook, self.machine_service)
        self.results_tab = ResultsTab(self.notebook, self.analysis_service)
        self.scheduler_tab = SchedulerTab(self.notebook, self.scheduler_service, self.machine_service)
        
        # Add tabs to notebook
        self.notebook.add(self.analysis_tab.frame, text="🔍 Analysis")
        self.notebook.add(self.machine_tab.frame, text="🏭 Machine Management")
        self.notebook.add(self.results_tab.frame, text="📊 Results")
        self.notebook.add(self.scheduler_tab.frame, text="📅 Scheduler")
        
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
        # Create menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="JMS Configuration", command=self._open_jms_config)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _open_jms_config(self):
        """Open the JMS configuration dialog"""
        JMSConfigDialog(self.root, self)
        
    def _show_about(self):
        """Show the about dialog"""
        messagebox.showinfo(
            "About NC Tool Analyzer",
            "NC Tool Analyzer\n\n"
            "A tool for analyzing NC programs and scheduling machine shop operations.\n\n"
            "Version 1.0"
        )
    
    def enable_jms_integration(self, base_url: str = "http://localhost:8080"):
        """
        Enable JMS integration
        
        Args:
            base_url: Base URL of the JMS API
            
        Returns:
            True if successful, False otherwise
        """
        if not self.jms_enabled:
            # Create new JMS service with provided URL
            self.jms_service = JMSService(self.scheduler_service, base_url)
            
            # Test connection
            if self.jms_service.test_connection():
                # Start polling
                self.jms_service.start_polling()
                self.jms_enabled = True
                
                # Pass JMS service to scheduler tab
                self.scheduler_tab.set_jms_service(self.jms_service)
                
                # Publish event
                event_system.publish("jms_enabled", f"JMS integration enabled with URL: {base_url}")
                
                return True
            else:
                tk.messagebox.showerror("JMS Connection Error",
                                      f"Failed to connect to JMS API at {base_url}")
                return False
        return True
    
    def disable_jms_integration(self):
        """Disable JMS integration"""
        if self.jms_enabled:
            # Stop polling
            self.jms_service.stop_polling()
            self.jms_enabled = False
            
            # Remove JMS service from scheduler tab
            self.scheduler_tab.set_jms_service(None)
            
            # Publish event
            event_system.publish("jms_disabled", "JMS integration disabled")