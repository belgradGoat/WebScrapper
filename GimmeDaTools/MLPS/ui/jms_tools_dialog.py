"""
JMS Tools Dialog
Dialog for accessing JMS tools and utilities
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import os
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Check if JMS modules are available
try:
    from services.jms.jms_client import JMSClient
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = True
except ImportError:
    JMS_AVAILABLE = False
    REQUESTS_AVAILABLE = False

class JMSToolsDialog:
    """Dialog for accessing JMS tools and utilities"""
    
    def __init__(self, parent, jms_service=None, initial_tab=0):
        """
        Initialize the JMS tools dialog
        
        Args:
            parent: Parent widget
            jms_service: JMSService instance (optional)
            initial_tab: Initial tab to select (0=Monitoring, 1=Testing, 2=Integration)
        """
        self.parent = parent
        self.jms_service = jms_service
        self.initial_tab = initial_tab
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("JMS Tools")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Check if JMS is available
        if not JMS_AVAILABLE:
            self._show_jms_unavailable()
            return
            
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Get JMS URL from service if available
        self.jms_url = tk.StringVar(value="https://10.164.181.100")
        if self.jms_service and hasattr(self.jms_service, 'base_url'):
            self.jms_url.set(self.jms_service.base_url)
        
        # Get cell ID (default to EMC.0520)
        self.cell_id = tk.StringVar(value="EMC.0520")
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the UI components"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="JMS Tools",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Connection settings frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection Settings", padding=10)
        conn_frame.pack(fill=tk.X, pady=10)
        
        # JMS URL
        url_frame = ttk.Frame(conn_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="JMS API URL:").pack(side=tk.LEFT)
        ttk.Entry(url_frame, textvariable=self.jms_url, width=40).pack(side=tk.LEFT, padx=5)
        
        # Cell ID
        cell_frame = ttk.Frame(conn_frame)
        cell_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cell_frame, text="Cell ID:").pack(side=tk.LEFT)
        ttk.Entry(cell_frame, textvariable=self.cell_id, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(cell_frame, text="Get Cells", command=self._get_cells).pack(side=tk.LEFT, padx=5)
        
        # Test connection button
        ttk.Button(
            conn_frame,
            text="Test Connection",
            command=self._test_connection
        ).pack(pady=10)
        
        # Tools frame
        tools_frame = ttk.LabelFrame(main_frame, text="JMS Tools", padding=10)
        tools_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a notebook for different tool categories
        self.notebook = ttk.Notebook(tools_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Monitoring tab
        monitoring_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(monitoring_tab, text="Monitoring")
        
        ttk.Label(
            monitoring_tab,
            text="Monitor robotic cell status in real-time",
            font=("Arial", 10, "italic")
        ).pack(pady=(0, 10))
        
        # Monitoring options
        mon_options_frame = ttk.Frame(monitoring_tab)
        mon_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(mon_options_frame, text="Polling interval (seconds):").pack(side=tk.LEFT)
        self.polling_interval = tk.StringVar(value="30")
        ttk.Entry(mon_options_frame, textvariable=self.polling_interval, width=5).pack(side=tk.LEFT, padx=5)
        
        # Start monitoring button
        ttk.Button(
            monitoring_tab,
            text="Start Cell Monitor",
            command=self._start_cell_monitor
        ).pack(pady=10)
        
        # Testing tab
        testing_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(testing_tab, text="Testing")
        
        ttk.Label(
            testing_tab,
            text="Test various robotic cell operations",
            font=("Arial", 10, "italic")
        ).pack(pady=(0, 10))
        
        # Test options
        test_options_frame = ttk.Frame(testing_tab)
        test_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(test_options_frame, text="Test:").pack(side=tk.LEFT)
        self.test_type = tk.StringVar(value="all")
        test_combo = ttk.Combobox(test_options_frame, textvariable=self.test_type, width=15)
        test_combo['values'] = ('all', 'cells', 'details', 'robot', 'machines', 'orders')
        test_combo.pack(side=tk.LEFT, padx=5)
        
        # Run test button
        ttk.Button(
            testing_tab,
            text="Run Cell Tests",
            command=self._run_cell_tests
        ).pack(pady=10)
        
        # Integration tab
        integration_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(integration_tab, text="Integration")
        
        ttk.Label(
            integration_tab,
            text="Run complete integration test with robotic cell",
            font=("Arial", 10, "italic")
        ).pack(pady=(0, 10))
        
        # Integration options
        int_options_frame = ttk.Frame(integration_tab)
        int_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(int_options_frame, text="Monitoring time (seconds):").pack(side=tk.LEFT)
        self.monitoring_time = tk.StringVar(value="60")
        ttk.Entry(int_options_frame, textvariable=self.monitoring_time, width=5).pack(side=tk.LEFT, padx=5)
        
        # Run integration test button
        ttk.Button(
            integration_tab,
            text="Run Integration Test",
            command=self._run_integration_test
        ).pack(pady=10)
        
        # Select the initial tab
        self.notebook.select(self.initial_tab)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(
            status_frame,
            text="Ready",
            foreground="blue"
        )
        self.status_label.pack(fill=tk.X)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
    
    def _show_jms_unavailable(self):
        """Show message that JMS is unavailable"""
        logger.warning("JMS is unavailable")
        
        # Clear the dialog
        for widget in self.dialog.winfo_children():
            widget.destroy()
            
        # Show message
        message_frame = ttk.Frame(self.dialog, padding=20)
        message_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            message_frame,
            text="JMS Tools Unavailable",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))
        
        if not JMS_AVAILABLE:
            # JMS modules not found
            message_text = "JMS modules not found. JMS tools will not be available."
        else:
            # Requests module not found
            message_text = "The Python 'requests' package is required for JMS tools.\n\n" \
                          "Please install it using pip:\n" \
                          "pip install requests\n\n" \
                          "You can still use the application with mock JMS functionality."
        
        ttk.Label(
            message_frame,
            text=message_text,
            justify=tk.CENTER
        ).pack(pady=20)
        
        ttk.Button(
            message_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(pady=20)
    
    def _update_status(self, message, color="blue"):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.dialog.update_idletasks()
    
    def _test_connection(self):
        """Test connection to JMS API"""
        url = self.jms_url.get()
        
        if not url:
            messagebox.showerror("Error", "Please enter a JMS API URL")
            return
        
        self._update_status("Testing connection...", "blue")
        
        try:
            # Create JMS client
            client = JMSClient(url)
            
            # Test connection
            if client.test_connection():
                self._update_status("Connection successful!", "green")
                messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
            else:
                self._update_status("Connection failed", "red")
                messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
        except Exception as e:
            self._update_status(f"Error: {str(e)}", "red")
            messagebox.showerror("Error", f"Error testing connection: {str(e)}")
    
    def _get_cells(self):
        """Get available cells from JMS API"""
        url = self.jms_url.get()
        
        if not url:
            messagebox.showerror("Error", "Please enter a JMS API URL")
            return
        
        self._update_status("Getting cells...", "blue")
        
        try:
            # Create JMS client
            client = JMSClient(url)
            
            # Get cells
            cells = client.cell.get_all_cells()
            
            if not cells:
                self._update_status("No cells found", "red")
                messagebox.showinfo("Cells", "No cells found")
                return
            
            # Create cell selection dialog
            cell_dialog = tk.Toplevel(self.dialog)
            cell_dialog.title("Select Cell")
            cell_dialog.geometry("400x300")
            cell_dialog.transient(self.dialog)
            cell_dialog.grab_set()
            
            # Center the dialog
            cell_dialog.update_idletasks()
            width = cell_dialog.winfo_width()
            height = cell_dialog.winfo_height()
            x = (cell_dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (cell_dialog.winfo_screenheight() // 2) - (height // 2)
            cell_dialog.geometry(f"+{x}+{y}")
            
            # Create listbox
            frame = ttk.Frame(cell_dialog, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="Select a cell:").pack(pady=(0, 5))
            
            # Create listbox with scrollbar
            list_frame = ttk.Frame(frame)
            list_frame.pack(fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(list_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(list_frame)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Configure scrollbar
            listbox.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=listbox.yview)
            
            # Add cells to listbox
            cell_map = {}
            for cell in cells:
                cell_id = cell.get('id')
                cell_name = cell.get('name', 'Unknown')
                display_text = f"{cell_name} (ID: {cell_id})"
                listbox.insert(tk.END, display_text)
                cell_map[display_text] = cell_id
            
            # Button frame
            button_frame = ttk.Frame(frame)
            button_frame.pack(fill=tk.X, pady=10)
            
            def on_select():
                selection = listbox.curselection()
                if selection:
                    selected_text = listbox.get(selection[0])
                    selected_id = cell_map.get(selected_text)
                    if selected_id:
                        self.cell_id.set(selected_id)
                        self._update_status(f"Selected cell: {selected_id}", "green")
                cell_dialog.destroy()
            
            ttk.Button(button_frame, text="Select", command=on_select).pack(side=tk.RIGHT, padx=5)
            ttk.Button(button_frame, text="Cancel", command=cell_dialog.destroy).pack(side=tk.RIGHT)
            
            self._update_status("Got cells", "green")
            
        except Exception as e:
            self._update_status(f"Error: {str(e)}", "red")
            messagebox.showerror("Error", f"Error getting cells: {str(e)}")
    
    def _start_cell_monitor(self):
        """Start the robotic cell monitor"""
        url = self.jms_url.get()
        cell_id = self.cell_id.get()
        interval = self.polling_interval.get()
        
        if not url or not cell_id:
            messagebox.showerror("Error", "Please enter JMS API URL and Cell ID")
            return
        
        try:
            interval = int(interval)
        except ValueError:
            messagebox.showerror("Error", "Polling interval must be a number")
            return
        
        self._update_status("Starting cell monitor...", "blue")
        
        # Get the path to the monitor script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "tools", "robotic_cell_monitor.py")
        
        # Check if script exists
        if not os.path.exists(script_path):
            self._update_status("Monitor script not found", "red")
            messagebox.showerror("Error", f"Monitor script not found at {script_path}")
            return
        
        # Build command
        cmd = [sys.executable, script_path, "--url", url, "--cell", cell_id, "--interval", str(interval)]
        
        # Run in a separate thread to avoid blocking the UI
        def run_monitor():
            try:
                subprocess.Popen(cmd)
                self._update_status("Cell monitor started", "green")
            except Exception as e:
                self._update_status(f"Error: {str(e)}", "red")
                messagebox.showerror("Error", f"Error starting cell monitor: {str(e)}")
        
        threading.Thread(target=run_monitor).start()
    
    def _run_cell_tests(self):
        """Run robotic cell tests"""
        url = self.jms_url.get()
        cell_id = self.cell_id.get()
        test_type = self.test_type.get()
        
        if not url:
            messagebox.showerror("Error", "Please enter JMS API URL")
            return
        
        if test_type != "cells" and not cell_id:
            messagebox.showerror("Error", "Please enter Cell ID")
            return
        
        self._update_status("Running cell tests...", "blue")
        
        # Get the path to the tester script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "tools", "robotic_cell_tester.py")
        
        # Check if script exists
        if not os.path.exists(script_path):
            self._update_status("Tester script not found", "red")
            messagebox.showerror("Error", f"Tester script not found at {script_path}")
            return
        
        # Build command
        cmd = [sys.executable, script_path, "--url", url, "--test", test_type]
        if cell_id and test_type != "cells":
            cmd.extend(["--cell", cell_id])
        
        # Run in a separate thread to avoid blocking the UI
        def run_tests():
            try:
                subprocess.Popen(cmd)
                self._update_status("Cell tests started", "green")
            except Exception as e:
                self._update_status(f"Error: {str(e)}", "red")
                messagebox.showerror("Error", f"Error running cell tests: {str(e)}")
        
        threading.Thread(target=run_tests).start()
    
    def _run_integration_test(self):
        """Run robotic cell integration test"""
        url = self.jms_url.get()
        cell_id = self.cell_id.get()
        monitoring_time = self.monitoring_time.get()
        
        if not url:
            messagebox.showerror("Error", "Please enter JMS API URL")
            return
        
        try:
            monitoring_time = int(monitoring_time)
        except ValueError:
            messagebox.showerror("Error", "Monitoring time must be a number")
            return
        
        self._update_status("Running integration test...", "blue")
        
        # Get the path to the integration script
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  "tools", "robotic_cell_integration.py")
        
        # Check if script exists
        if not os.path.exists(script_path):
            self._update_status("Integration script not found", "red")
            messagebox.showerror("Error", f"Integration script not found at {script_path}")
            return
        
        # Build command
        cmd = [sys.executable, script_path, "--url", url, "--time", str(monitoring_time)]
        if cell_id:
            cmd.extend(["--cell", cell_id])
        
        # Run in a separate thread to avoid blocking the UI
        def run_integration():
            try:
                subprocess.Popen(cmd)
                self._update_status("Integration test started", "green")
            except Exception as e:
                self._update_status(f"Error: {str(e)}", "red")
                messagebox.showerror("Error", f"Error running integration test: {str(e)}")
        
        threading.Thread(target=run_integration).start()

def show_jms_tools_dialog(parent, jms_service=None, initial_tab=0):
    """
    Show the JMS tools dialog
    
    Args:
        parent: Parent widget
        jms_service: JMSService instance (optional)
        initial_tab: Initial tab to select (0=Monitoring, 1=Testing, 2=Integration)
    
    Returns:
        JMSToolsDialog instance
    """
    dialog = JMSToolsDialog(parent, jms_service, initial_tab)
    return dialog

if __name__ == "__main__":
    # For testing
    root = tk.Tk()
    root.title("JMS Tools Test")
    root.geometry("200x100")
    
    ttk.Button(root, text="Show JMS Tools", command=lambda: show_jms_tools_dialog(root, initial_tab=0)).pack(pady=20)
    
    root.mainloop()