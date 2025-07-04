"""
Machine Tab for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk, messagebox

from models.machine import Machine
from utils.event_system import event_system


class MachineTab:
    """
    Machine management tab for the NC Tool Analyzer application
    """
    def __init__(self, parent, machine_service):
        """
        Initialize the machine tab
        
        Args:
            parent: Parent widget
            machine_service: MachineService instance
        """
        self.parent = parent
        self.machine_service = machine_service
        
        # Create frame
        self.frame = ttk.Frame(parent)
        
        # Setup UI components
        self.setup_ui()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Add machine section
        add_frame = ttk.LabelFrame(self.frame, text="Add New Machine", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Machine details grid
        details_frame = ttk.Frame(add_frame)
        details_frame.pack(fill=tk.X)
        
        # Variables for machine input
        self.machine_vars = {
            'id': tk.StringVar(),
            'name': tk.StringVar(),
            'type': tk.StringVar(value="Machining Center"),
            'location': tk.StringVar(),
            'ip': tk.StringVar(),
            'tnc_folder': tk.StringVar(),
            'max_slots': tk.StringVar(value="130"),
            'notes': tk.StringVar()
        }
        
        # Create input fields
        fields = [
            ("Machine ID:", 'id', 0, 0),
            ("Name:", 'name', 0, 2),
            ("Type:", 'type', 1, 0),
            ("Location:", 'location', 1, 2),
            ("IP Address:", 'ip', 2, 0),
            ("TNC Folder:", 'tnc_folder', 2, 2),
            ("Max Slots:", 'max_slots', 3, 0),
            ("Notes:", 'notes', 3, 2)
        ]
        
        for label, var_key, row, col in fields:
            ttk.Label(details_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            ttk.Entry(details_frame, textvariable=self.machine_vars[var_key], width=25).grid(row=row, column=col+1, sticky=tk.W, padx=5, pady=2)
        
        # Add machine button
        ttk.Button(add_frame, text="➕ Add Machine", command=self.add_machine).pack(pady=10)
        
        # Machine list
        list_frame = ttk.LabelFrame(self.frame, text="Configured Machines", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Machine treeview
        columns = ('ID', 'Name', 'IP', 'Tools', 'Last Updated', 'Status')
        self.machine_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.machine_tree.heading(col, text=col)
            self.machine_tree.column(col, width=100)
        
        self.machine_tree.pack(fill=tk.BOTH, expand=True)
        
        # Machine management buttons
        machine_buttons = ttk.Frame(list_frame)
        machine_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(machine_buttons, text="🧪 Test", command=self.test_button).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(machine_buttons, text="📥 Download Tools", command=self.download_selected_machine).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(machine_buttons, text="✏️ Edit", command=self.edit_selected_machine).pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(machine_buttons, text="🗑️ Delete", command=self.delete_selected_machine).pack(side=tk.LEFT, padx=(0,5))
        
        # Refresh machine list
        self.refresh_machine_list()
        
    def _setup_event_handlers(self):
        """Set up event handlers for tab events"""
        # Update machine list when machines are loaded or updated
        event_system.subscribe("machines_loaded", lambda _: self.refresh_machine_list())
        event_system.subscribe("machine_added", lambda _: self.refresh_machine_list())
        event_system.subscribe("machine_updated", lambda _: self.refresh_machine_list())
        event_system.subscribe("machine_deleted", lambda _: self.refresh_machine_list())
        
    def add_machine(self):
        """Add new machine to database"""
        # Validate required fields
        required = ['id', 'name', 'ip']
        for field in required:
            if not self.machine_vars[field].get().strip():
                messagebox.showerror("Error", f"Please fill in {field.replace('_', ' ').title()}")
                return
        
        machine_id = self.machine_vars['id'].get().strip().upper()
        
        # Check if machine exists
        if self.machine_service.get_machine(machine_id):
            if not messagebox.askyesno("Confirm", f"Machine {machine_id} already exists. Overwrite?"):
                return
        
        # Create machine object
        machine = Machine(
            machine_id=machine_id,
            name=self.machine_vars['name'].get().strip(),
            machine_type=self.machine_vars['type'].get().strip(),
            location=self.machine_vars['location'].get().strip(),
            ip_address=self.machine_vars['ip'].get().strip(),
            tnc_folder=self.machine_vars['tnc_folder'].get().strip(),
            max_slots=int(self.machine_vars['max_slots'].get() or 130),
            notes=self.machine_vars['notes'].get().strip()
        )
        
        # Add machine to database
        self.machine_service.add_machine(machine)
        
        # Clear form
        for var in self.machine_vars.values():
            var.set("")
        self.machine_vars['type'].set("Machining Center")
        self.machine_vars['max_slots'].set("130")
        
        messagebox.showinfo("Success", f"Machine {machine_id} added successfully!")
        
    def refresh_machine_list(self):
        """Refresh the machine list display"""
        # Clear existing items
        for item in self.machine_tree.get_children():
            self.machine_tree.delete(item)
        
        # Add machines
        machines = self.machine_service.get_all_machines()
        for machine_id, machine in machines.items():
            available_count = len(machine.physical_tools)
            locked_count = len(machine.locked_tools)
            
            # Enhanced status with locked tool info
            if available_count > 0:
                if locked_count > 0:
                    status = f'⚠️ {available_count} OK, {locked_count} Locked'
                else:
                    status = f'✅ {available_count} Ready'
            else:
                status = '❌ No Tools'
            
            # Only show locked count if there are actually locked tools
            tool_count_display = str(available_count)
            if locked_count > 0:
                tool_count_display = f"{available_count}+{locked_count}"
            
            self.machine_tree.insert('', tk.END, values=(
                machine.machine_id,
                machine.name,
                machine.ip_address,
                tool_count_display,
                machine.last_updated or "Never",
                status
            ))
            
    def test_button(self):
        """Test tree selection functionality"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showinfo("Test", "No machine selected in tree. Please click on a machine first.")
        else:
            try:
                machine_id = self.machine_tree.item(selection[0])['values'][0]
                machine = self.machine_service.get_machine(machine_id)
                
                if machine:
                    msg = f"Selected machine: {machine_id}\n"
                    msg += f"Name: {machine.name}\n"
                    msg += f"IP: {machine.ip_address}\n"
                    msg += f"Tools: {len(machine.physical_tools)} available, {len(machine.locked_tools)} locked\n"
                    msg += f"Last Updated: {machine.last_updated or 'Never'}"
                    
                    messagebox.showinfo("Machine Info", msg)
                else:
                    messagebox.showerror("Error", f"Machine {machine_id} not found in database")
                    
            except Exception as e:
                messagebox.showerror("Test Error", f"Error reading selection: {str(e)}")
                
    def download_selected_machine(self):
        """Download tools from selected machine"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine first")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        
        # Start download in a separate thread
        self._start_background_task(lambda: self._download_machine_task(machine_id))
        
    def _download_machine_task(self, machine_id):
        """Background task for downloading from a machine"""
        success, message = self.machine_service.download_from_machine(machine_id)
        
        # Update UI in main thread
        self.frame.after(0, lambda: self._download_complete(machine_id, success, message))
        
    def _download_complete(self, machine_id, success, message):
        """Called when download is complete"""
        if success:
            messagebox.showinfo("Success", f"{machine_id}: {message}")
        else:
            messagebox.showerror("Error", f"{machine_id}: {message}")
            
    def edit_selected_machine(self):
        """Edit selected machine"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine first")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        machine = self.machine_service.get_machine(machine_id)
        
        if not machine:
            messagebox.showerror("Error", f"Machine {machine_id} not found in database")
            return
        
        # Populate form with existing data
        self.machine_vars['id'].set(machine.machine_id)
        self.machine_vars['name'].set(machine.name)
        self.machine_vars['type'].set(machine.machine_type)
        self.machine_vars['location'].set(machine.location)
        self.machine_vars['ip'].set(machine.ip_address)
        self.machine_vars['tnc_folder'].set(machine.tnc_folder)
        self.machine_vars['max_slots'].set(str(machine.max_slots))
        self.machine_vars['notes'].set(machine.notes)
        
    def delete_selected_machine(self):
        """Delete selected machine"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine first")
            return
        
        machine_id = self.machine_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete machine {machine_id}?"):
            success = self.machine_service.delete_machine(machine_id)
            if success:
                messagebox.showinfo("Success", f"Machine {machine_id} deleted")
            else:
                messagebox.showerror("Error", f"Failed to delete machine {machine_id}")
                
    def _start_background_task(self, task_func):
        """
        Start a background task in a separate thread
        
        Args:
            task_func: Function to run in the background
        """
        import threading
        thread = threading.Thread(target=task_func, daemon=True)
        thread.start()