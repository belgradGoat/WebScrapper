"""
JMS Configuration Dialog
"""
import tkinter as tk
from tkinter import ttk, messagebox

# Check if JMS modules are available
try:
    from services.jms.jms_auth import REQUESTS_AVAILABLE
    JMS_AVAILABLE = True  # Module is available even if requests is not
except ImportError:
    JMS_AVAILABLE = False
    
import logging
logger = logging.getLogger(__name__)


class JMSConfigDialog:
    """Dialog for configuring JMS integration"""
    
    def __init__(self, parent, jms_service):
        """
        Initialize the JMS configuration dialog
        
        Args:
            parent: Parent widget
            jms_service: JMSService module or instance
        """
        self.parent = parent
        self.jms_service = jms_service
        
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
            
        # Log JMS availability
        logger.info(f"JMS config dialog initialized, REQUESTS_AVAILABLE={REQUESTS_AVAILABLE}")
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create variables with default values
        self.jms_url = tk.StringVar(value="http://localhost:8080")
        self.jms_enabled = tk.BooleanVar(value=hasattr(self.jms_service, 'jms_enabled') and self.jms_service.jms_enabled)
        self.jms_username = tk.StringVar(value="")
        self.jms_password = tk.StringVar(value="")
        
        # Load current values from JMS service if available
        self._load_current_values()
        
        # Create UI
        self._create_ui()
        
    def _load_current_values(self):
        """Load current values from JMS service"""
        try:
            # Check if JMS service has get_base_url method (JMSServiceModule)
            if hasattr(self.jms_service, 'get_base_url'):
                base_url = self.jms_service.get_base_url()
                if base_url:
                    self.jms_url.set(base_url)
                    logger.info(f"Loaded base URL from JMS service: {base_url}")
                
                # Load username if available
                username = self.jms_service.get_username()
                if username:
                    self.jms_username.set(username)
                    logger.info(f"Loaded username from JMS service: {username}")
                
                # Load password if available
                password = self.jms_service.get_password()
                if password:
                    self.jms_password.set(password)
                    logger.info("Loaded password from JMS service")
            
            # Check if JMS service has base_url attribute directly
            elif hasattr(self.jms_service, 'base_url'):
                base_url = self.jms_service.base_url
                if base_url:
                    self.jms_url.set(base_url)
                    logger.info(f"Loaded base URL from JMS service attribute: {base_url}")
                
                # Load username if available
                if hasattr(self.jms_service, 'username') and self.jms_service.username:
                    self.jms_username.set(self.jms_service.username)
                    logger.info(f"Loaded username from JMS service attribute: {self.jms_service.username}")
                
                # Load password if available
                if hasattr(self.jms_service, 'password') and self.jms_service.password:
                    self.jms_password.set(self.jms_service.password)
                    logger.info("Loaded password from JMS service attribute")
            
            logger.info(f"JMS configuration loaded: URL={self.jms_url.get()}, Username={self.jms_username.get() != ''}")
        except Exception as e:
            logger.error(f"Error loading current values from JMS service: {str(e)}")
    
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
        
        # JMS Authentication
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication", padding=10)
        auth_frame.pack(fill=tk.X, pady=10)
        
        # Username
        username_frame = ttk.Frame(auth_frame)
        username_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(username_frame, text="Username:").pack(side=tk.LEFT)
        ttk.Entry(username_frame, textvariable=self.jms_username, width=30).pack(side=tk.LEFT, padx=5)
        
        # Password
        password_frame = ttk.Frame(auth_frame)
        password_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(password_frame, text="Password:").pack(side=tk.LEFT)
        password_entry = ttk.Entry(password_frame, textvariable=self.jms_password, width=30, show="*")
        password_entry.pack(side=tk.LEFT, padx=5)
        
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
        logger.info(f"Toggling JMS integration, current state: {self.jms_enabled.get()}")
        
        if self.jms_enabled.get():
            # Enable JMS
            if hasattr(self.jms_service, 'enable_jms'):
                # Validate and normalize URL
                url = self.jms_url.get().strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url
                    self.jms_url.set(url)
                
                logger.info(f"Enabling JMS with URL: {url}")
                
                # Get username and password if provided
                username = self.jms_username.get().strip() if self.jms_username.get() else None
                password = self.jms_password.get() if self.jms_password.get() else None
                
                if username and password:
                    logger.info(f"Using username authentication: {username}")
                    success = self.jms_service.enable_jms(url, username, password)
                else:
                    logger.info("Using client credentials authentication")
                    success = self.jms_service.enable_jms(url)
                    
                logger.info(f"JMS enable result: {success}")
            else:
                # Fallback for direct JMSService instance
                try:
                    # Update the JMS service with the new URL, username, and password
                    url = self.jms_url.get().strip()
                    if not url.startswith(('http://', 'https://')):
                        url = 'http://' + url
                        self.jms_url.set(url)
                    
                    username = self.jms_username.get().strip() if self.jms_username.get() else None
                    password = self.jms_password.get() if self.jms_password.get() else None
                    
                    # Update JMS service attributes if available
                    if hasattr(self.jms_service, 'base_url'):
                        self.jms_service.base_url = url
                        logger.info(f"Updated JMS service base URL to: {url}")
                    
                    if username and hasattr(self.jms_service, 'username'):
                        self.jms_service.username = username
                        logger.info(f"Updated JMS service username to: {username}")
                    
                    if password and hasattr(self.jms_service, 'password'):
                        self.jms_service.password = password
                        logger.info("Updated JMS service password")
                    
                    logger.info("Testing JMS connection")
                    connection_result = self.jms_service.test_connection()
                    logger.info(f"Connection test result: {connection_result}")
                    
                    if connection_result or not REQUESTS_AVAILABLE:
                        logger.info("Starting JMS polling")
                        self.jms_service.start_polling()
                        success = True
                    else:
                        success = False
                except Exception as e:
                    logger.error(f"Error enabling JMS integration: {str(e)}")
                    messagebox.showerror("JMS Error", f"Error enabling JMS integration: {str(e)}")
                    success = False
                    
            # If requests is not available but JMS modules are, enable anyway with mock functionality
            if not success and not REQUESTS_AVAILABLE:
                logger.info("Using mock JMS functionality")
                success = True
                messagebox.showinfo("JMS Information", "Using mock JMS functionality (requests module not available)")
                    
            if not success:
                self.jms_enabled.set(False)
        else:
            # Disable JMS
            logger.info("Disabling JMS integration")
            if hasattr(self.jms_service, 'disable_jms'):
                self.jms_service.disable_jms()
            else:
                # Fallback for direct JMSService instance
                try:
                    self.jms_service.stop_polling()
                except Exception as e:
                    logger.error(f"Error disabling JMS integration: {str(e)}")
                    messagebox.showerror("JMS Error", f"Error disabling JMS integration: {str(e)}")
            
        # Update status
        self._update_status()
        
    def _test_connection(self):
        """Test connection to JMS API"""
        logger.info("Testing JMS connection")
        
        if not JMS_AVAILABLE:
            messagebox.showerror("Error", "JMS integration is not available. Please install the 'requests' package.")
            return
            
        # If requests is not available but JMS modules are, show mock message
        if not REQUESTS_AVAILABLE:
            logger.info("Using mock connection test")
            messagebox.showinfo("Connection Test", "Using mock JMS functionality (requests module not available)")
            return
            
        try:
            # Test connection using existing JMS service
            if hasattr(self.jms_service, 'test_connection'):
                # For JMSServiceModule
                # Validate and normalize URL
                url = self.jms_url.get().strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url
                    self.jms_url.set(url)
                
                logger.info(f"Testing connection to {url}")
                
                # Get username and password if provided
                username = self.jms_username.get().strip() if self.jms_username.get() else None
                password = self.jms_password.get() if self.jms_password.get() else None
                
                # Update JMS service base URL if it has the attribute
                if hasattr(self.jms_service, 'base_url'):
                    self.jms_service.base_url = url
                    logger.info(f"Updated JMS service base URL to: {url}")
                
                # If the JMS service has a save_config method, call it
                if hasattr(self.jms_service, '_save_config'):
                    self.jms_service._save_config()
                    logger.info("Saved JMS configuration")
                
                # Create a new JMS service with the provided credentials for testing
                if hasattr(self.jms_service, 'username') and hasattr(self.jms_service, 'password'):
                    # Store original credentials
                    orig_username = self.jms_service.username
                    orig_password = self.jms_service.password
                    
                    # Set new credentials for testing
                    if username and password:
                        self.jms_service.username = username
                        self.jms_service.password = password
                        logger.info(f"Using username authentication for test: {username}")
                    
                    # Test connection
                    if self.jms_service.test_connection():
                        logger.info("Connection test successful")
                        messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
                    else:
                        logger.warning("Connection test failed")
                        messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
                    
                    # Restore original credentials
                    self.jms_service.username = orig_username
                    self.jms_service.password = orig_password
                else:
                    # Fall back to simple test
                    if self.jms_service.test_connection():
                        logger.info("Connection test successful")
                        messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
                    else:
                        logger.warning("Connection test failed")
                        messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
            else:
                # Create temporary JMS service for testing
                logger.info("Creating temporary JMS service for testing")
                from services.jms_service import JMSService
                from services.scheduler_service import SchedulerService
                
                # Try to get scheduler service from the JMS service if available
                if hasattr(self.jms_service, 'scheduler_service'):
                    scheduler_service = self.jms_service.scheduler_service
                    logger.info("Using scheduler service from JMS service")
                else:
                    # Create a temporary scheduler service
                    logger.info("Creating temporary scheduler service")
                    from services.machine_service import MachineService
                    machine_service = MachineService()
                    scheduler_service = SchedulerService(machine_service)
                
                # Get username and password if provided
                url = self.jms_url.get().strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'http://' + url
                    self.jms_url.set(url)
                
                username = self.jms_username.get() if self.jms_username.get() else None
                password = self.jms_password.get() if self.jms_password.get() else None
                
                # Create temporary JMS service
                logger.info(f"Creating temporary JMS service with URL: {url}")
                if username and password:
                    logger.info(f"Using username authentication for test: {username}")
                    temp_jms_service = JMSService(scheduler_service, url, username=username, password=password)
                else:
                    logger.info("Using client credentials authentication for test")
                    temp_jms_service = JMSService(scheduler_service, url)
                
                # Test connection
                logger.info("Testing connection with temporary JMS service")
                connection_result = temp_jms_service.test_connection()
                if connection_result:
                    logger.info("Connection test successful")
                    messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
                    
                    # If the test is successful, update the main JMS service if it has the attributes
                    if hasattr(self.jms_service, 'base_url'):
                        self.jms_service.base_url = url
                        logger.info(f"Updated JMS service base URL to: {url}")
                    
                    if username and hasattr(self.jms_service, 'username'):
                        self.jms_service.username = username
                        logger.info(f"Updated JMS service username to: {username}")
                    
                    if password and hasattr(self.jms_service, 'password'):
                        self.jms_service.password = password
                        logger.info("Updated JMS service password")
                    
                    # If the JMS service has a save_config method, call it
                    if hasattr(self.jms_service, '_save_config'):
                        self.jms_service._save_config()
                        logger.info("Saved JMS configuration")
                else:
                    logger.warning("Connection test failed")
                    messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
        except Exception as e:
            logger.error(f"Error testing connection: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            messagebox.showerror("Error", f"Error testing connection: {str(e)}")
            
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
            text="JMS Integration Unavailable",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 20))
        
        if not JMS_AVAILABLE:
            # JMS modules not found
            message_text = "JMS modules not found. JMS integration will not be available."
        else:
            # Requests module not found
            message_text = "The Python 'requests' package is required for JMS integration.\n\n" \
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