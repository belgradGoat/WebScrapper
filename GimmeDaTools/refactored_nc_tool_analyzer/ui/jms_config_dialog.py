"""
JMS Configuration Dialog
"""
import tkinter as tk
from tkinter import ttk, messagebox

# Check if JMS modules are available
try:
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = REQUESTS_AVAILABLE
except ImportError:
    JMS_AVAILABLE = False


class JMSConfigDialog:
    """Dialog for configuring JMS integration"""
    
    def __init__(self, parent, main_window):
        """
        Initialize the JMS configuration dialog
        
        Args:
            parent: Parent widget
            main_window: MainWindow instance
        """
        self.parent = parent
        self.main_window = main_window
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("JMS Integration Configuration")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
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
        
        # Create variables
        self.jms_url = tk.StringVar(value="http://localhost:8080")
        self.jms_enabled = tk.BooleanVar(value=self.main_window.jms_enabled)
        
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
            text="JMS Integration Configuration",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # JMS URL
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="JMS API URL:").pack(side=tk.LEFT)
        ttk.Entry(url_frame, textvariable=self.jms_url, width=40).pack(side=tk.LEFT, padx=5)
        
        # Enable/Disable JMS
        enable_frame = ttk.Frame(main_frame)
        enable_frame.pack(fill=tk.X, pady=10)
        
        ttk.Checkbutton(
            enable_frame, 
            text="Enable JMS Integration",
            variable=self.jms_enabled,
            command=self._toggle_jms
        ).pack(side=tk.LEFT)
        
        # Status
        self.status_label = ttk.Label(
            main_frame,
            text="JMS Integration is disabled",
            foreground="red"
        )
        self.status_label.pack(pady=10)
        
        # Update status
        self._update_status()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(
            button_frame,
            text="Test Connection",
            command=self._test_connection
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
    def _toggle_jms(self):
        """Toggle JMS integration"""
        if self.jms_enabled.get():
            # Enable JMS
            success = self.main_window.enable_jms_integration(self.jms_url.get())
            if not success:
                self.jms_enabled.set(False)
        else:
            # Disable JMS
            self.main_window.disable_jms_integration()
            
        # Update status
        self._update_status()
        
    def _test_connection(self):
        """Test connection to JMS API"""
        if not JMS_AVAILABLE:
            messagebox.showerror("Error", "JMS integration is not available. Please install the 'requests' package.")
            return
            
        try:
            # Create temporary JMS service
            from services.jms_service import JMSService
            jms_service = JMSService(self.main_window.scheduler_service, self.jms_url.get())
            
            # Test connection
            if jms_service.test_connection():
                messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
            else:
                messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
        except Exception as e:
            messagebox.showerror("Error", f"Error testing connection: {str(e)}")
            
    def _show_jms_unavailable(self):
        """Show message that JMS is unavailable"""
        # Clear the dialog
        for widget in self.dialog.winfo_children():
            widget.destroy()
            
        # Show message
        message_frame = ttk.Frame(self.dialog, padding=20)
        message_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            message_frame,
            text="JMS Integration Unavailable",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))
        
        ttk.Label(
            message_frame,
            text="The Python 'requests' package is required for JMS integration.\n\n"
                 "Please install it using pip:\n"
                 "pip install requests",
            justify=tk.CENTER
        ).pack(pady=20)
        
        ttk.Button(
            message_frame,
            text="Close",
            command=self.dialog.destroy
        ).pack(pady=20)
            
    def _update_status(self):
        """Update status label"""
        if self.jms_enabled.get():
            self.status_label.config(
                text="JMS Integration is enabled",
                foreground="green"
            )
        else:
            self.status_label.config(
                text="JMS Integration is disabled",
                foreground="red"
            )