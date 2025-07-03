"""
Main Window for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk

from services.machine_service import MachineService
from services.analysis_service import AnalysisService
from services.scheduler_service import SchedulerService
from ui.analysis_tab import AnalysisTab
from ui.machine_tab import MachineTab
from ui.results_tab import ResultsTab
from ui.scheduler_tab import SchedulerTab
from utils.event_system import event_system


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
        
        # Setup UI
        self.setup_ui()
        
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