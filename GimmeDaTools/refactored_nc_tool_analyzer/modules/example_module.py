"""
Example Module for NC Tool Analyzer
Demonstrates how to create a custom module
"""
import logging
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Any

from module_system.module_interface import TabModuleInterface

logger = logging.getLogger(__name__)


class ExampleModule(TabModuleInterface):
    """Example module that provides a custom tab"""
    
    def __init__(self):
        """Initialize the module"""
        self.frame = None
        self.machine_service = None
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "example_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Example module that demonstrates how to create a custom tab"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["machine_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing example module")
        
        # Get the required services
        self.machine_service = service_registry.get_service("machine_service")
        if not self.machine_service:
            raise ValueError("Machine service not found")
    
    def get_tab(self, parent) -> Any:
        """Return the tab frame for this module"""
        logger.info("Creating example tab")
        
        # Create the tab frame
        self.frame = ttk.Frame(parent)
        
        # Add some content to the tab
        ttk.Label(self.frame, text="Example Module", font=('Arial', 16, 'bold')).pack(pady=20)
        ttk.Label(self.frame, text="This is an example module that demonstrates how to create a custom tab.").pack(pady=10)
        
        # Add a list of machines
        ttk.Label(self.frame, text="Machines:", font=('Arial', 12, 'bold')).pack(pady=10, anchor=tk.W, padx=20)
        
        # Create a frame for the machine list
        machine_frame = ttk.Frame(self.frame)
        machine_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(machine_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add a listbox
        machine_listbox = tk.Listbox(machine_frame, yscrollcommand=scrollbar.set)
        machine_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure the scrollbar
        scrollbar.config(command=machine_listbox.yview)
        
        # Add machines to the listbox
        machines = self.machine_service.get_all_machines()
        for machine_id in machines:
            machine = self.machine_service.get_machine(machine_id)
            machine_listbox.insert(tk.END, f"{machine.name} ({machine.machine_id})")
        
        # Add a button
        ttk.Button(self.frame, text="Refresh Machines", command=self._refresh_machines).pack(pady=20)
        
        return self.frame
    
    def _refresh_machines(self):
        """Refresh the machine list"""
        logger.info("Refreshing machines")
        tk.messagebox.showinfo("Example Module", "This is an example button action.")
    
    def get_tab_name(self) -> str:
        """Return the name of the tab"""
        return "Example"
    
    def get_tab_icon(self) -> str:
        """Return the icon for the tab"""
        return "🔌"
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down example module")
        # No specific shutdown needed