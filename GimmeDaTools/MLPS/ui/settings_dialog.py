"""
Settings Dialog for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk, messagebox

class SettingsDialog:
    """Dialog for application settings"""
    
    def __init__(self, parent, app_core):
        """
        Initialize the settings dialog
        
        Args:
            parent: Parent widget
            app_core: ApplicationCore instance
        """
        self.parent = parent
        self.app_core = app_core
        self.service_registry = app_core.get_service_registry()
        self.config_manager = app_core.get_config_manager()
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create UI
        self._create_ui()
        
    def _create_ui(self):
        """Create the UI components"""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self._create_general_tab()
        self._create_modules_tab()
        self._create_jms_tab()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self._save_and_close
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=self._save_settings
        ).pack(side=tk.RIGHT, padx=5)
        
    def _create_general_tab(self):
        """Create the general settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="General")
        
        # App name
        name_frame = ttk.Frame(tab)
        name_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(name_frame, text="Application Name:").pack(side=tk.LEFT)
        
        self.app_name_var = tk.StringVar(value=self.config_manager.get_value("app.name", "NC Tool Analyzer"))
        ttk.Entry(name_frame, textvariable=self.app_name_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # App version
        version_frame = ttk.Frame(tab)
        version_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(version_frame, text="Version:").pack(side=tk.LEFT)
        
        self.app_version_var = tk.StringVar(value=self.config_manager.get_value("app.version", "1.0.0"))
        ttk.Entry(version_frame, textvariable=self.app_version_var, width=20).pack(side=tk.LEFT, padx=5)
        
    def _create_modules_tab(self):
        """Create the modules settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Modules")
        
        # Create a frame with scrollbar
        frame_canvas = ttk.Frame(tab)
        frame_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Add a canvas
        canvas = tk.Canvas(frame_canvas)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure the canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Create a frame inside the canvas
        modules_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=modules_frame, anchor="nw")
        
        # Get all modules
        module_registry = self.app_core.get_module_registry()
        modules = module_registry.get_all_modules()
        
        # Module variables
        self.module_vars = {}
        
        # Add modules to the list
        for i, (module_name, module) in enumerate(modules.items()):
            frame = ttk.Frame(modules_frame)
            frame.pack(fill=tk.X, pady=5)
            
            # Module enabled checkbox
            enabled = self.config_manager.get_value(f"modules.{module_name}.enabled", True)
            var = tk.BooleanVar(value=enabled)
            self.module_vars[module_name] = var
            
            ttk.Checkbutton(
                frame,
                text=f"{module.get_name()} (v{module.get_version()})",
                variable=var
            ).pack(side=tk.LEFT)
            
            # Module description
            ttk.Label(
                frame,
                text=module.get_description(),
                foreground="gray"
            ).pack(side=tk.LEFT, padx=10)
            
    def _create_jms_tab(self):
        """Create the JMS settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="JMS")
        
        # Check if JMS is available
        jms_service = self.service_registry.get_service("jms_service")
        jms_service_module = self.service_registry.get_service("jms_service_module")
        
        if not jms_service and not jms_service_module:
            ttk.Label(
                tab,
                text="JMS integration is not available.\n\nPlease make sure the JMS modules are enabled.",
                justify=tk.CENTER
            ).pack(expand=True, pady=50)
            return
        
        # JMS enabled
        enabled_frame = ttk.Frame(tab)
        enabled_frame.pack(fill=tk.X, pady=10)
        
        # Get JMS enabled state
        jms_enabled = False
        if jms_service_module and hasattr(jms_service_module, 'jms_enabled'):
            jms_enabled = jms_service_module.jms_enabled
        
        self.jms_enabled_var = tk.BooleanVar(value=jms_enabled)
        ttk.Checkbutton(
            enabled_frame,
            text="Enable JMS Integration",
            variable=self.jms_enabled_var,
            command=self._toggle_jms
        ).pack(side=tk.LEFT)
        
        # JMS URL
        url_frame = ttk.Frame(tab)
        url_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(url_frame, text="JMS API URL:").pack(side=tk.LEFT)
        
        # Get JMS URL from config
        jms_url = self.config_manager.get_value("modules.jms_service_module.base_url", "http://localhost:8080")
        
        self.jms_url_var = tk.StringVar(value=jms_url)
        ttk.Entry(url_frame, textvariable=self.jms_url_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Test connection button
        ttk.Button(
            url_frame,
            text="Test Connection",
            command=self._test_jms_connection
        ).pack(side=tk.LEFT, padx=5)
        
        # Status
        status_frame = ttk.Frame(tab)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        
        status_text = "Disabled"
        status_color = "red"
        if jms_enabled:
            status_text = "Enabled"
            status_color = "green"
            
        self.jms_status_label = ttk.Label(
            status_frame,
            text=status_text,
            foreground=status_color
        )
        self.jms_status_label.pack(side=tk.LEFT, padx=5)
        
    def _toggle_jms(self):
        """Toggle JMS integration"""
        jms_service_module = self.service_registry.get_service("jms_service_module")
        if not jms_service_module:
            messagebox.showerror("Error", "JMS service module not available")
            self.jms_enabled_var.set(False)
            return
            
        if self.jms_enabled_var.get():
            # Enable JMS
            if hasattr(jms_service_module, 'enable_jms'):
                success = jms_service_module.enable_jms(self.jms_url_var.get())
                if success:
                    self.jms_status_label.config(text="Enabled", foreground="green")
                else:
                    self.jms_enabled_var.set(False)
                    self.jms_status_label.config(text="Disabled", foreground="red")
            else:
                messagebox.showerror("Error", "JMS service module does not support enabling")
                self.jms_enabled_var.set(False)
        else:
            # Disable JMS
            if hasattr(jms_service_module, 'disable_jms'):
                jms_service_module.disable_jms()
                self.jms_status_label.config(text="Disabled", foreground="red")
            else:
                messagebox.showerror("Error", "JMS service module does not support disabling")
                
    def _test_jms_connection(self):
        """Test connection to JMS API"""
        jms_service = self.service_registry.get_service("jms_service")
        jms_service_module = self.service_registry.get_service("jms_service_module")
        
        if jms_service and hasattr(jms_service, 'test_connection'):
            # Test using JMS service
            if jms_service.test_connection():
                messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
            else:
                messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
        elif jms_service_module and hasattr(jms_service_module, 'enable_jms'):
            # Test using JMS service module
            if jms_service_module.enable_jms(self.jms_url_var.get()):
                messagebox.showinfo("Connection Test", "Successfully connected to JMS API!")
                # Disable it again if it wasn't enabled before
                if not self.jms_enabled_var.get():
                    jms_service_module.disable_jms()
            else:
                messagebox.showerror("Connection Test", "Failed to connect to JMS API!")
        else:
            messagebox.showerror("Error", "JMS service not available")
            
    def _save_settings(self):
        """Save settings"""
        # Save general settings
        self.config_manager.set_value("app.name", self.app_name_var.get())
        self.config_manager.set_value("app.version", self.app_version_var.get())
        
        # Save module settings
        for module_name, var in self.module_vars.items():
            self.config_manager.set_value(f"modules.{module_name}.enabled", var.get())
            
        # Save JMS settings
        self.config_manager.set_value("modules.jms_service_module.base_url", self.jms_url_var.get())
        
        messagebox.showinfo("Settings", "Settings saved successfully")
        
    def _save_and_close(self):
        """Save settings and close dialog"""
        self._save_settings()
        self.dialog.destroy()