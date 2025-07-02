#!/usr/bin/env python3
"""
NC Tool Analyzer GUI
A complete tool analysis system with automatic machine communication
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import re
import json
import threading
from pathlib import Path
from datetime import datetime

class NCToolAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("NC Tool Analyzer")
        self.root.geometry("1200x800")
        
        # Data storage
        self.machine_database = self.load_machine_database()
        self.current_nc_analysis = None
        
        # Setup GUI
        self.setup_gui()
        
    def setup_gui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Analysis Tab
        self.setup_analysis_tab()
        
        # Machine Management Tab
        self.setup_machine_tab()
        
        # Results Tab
        self.setup_results_tab()
        
    def setup_analysis_tab(self):
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="🔍 Analysis")
        
        # Instructions
        instructions = ttk.LabelFrame(self.analysis_frame, text="Quick Start", padding=10)
        instructions.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(instructions, text="1. Add machines in 'Machine Management' tab", font=('Arial', 10)).pack(anchor=tk.W)
        ttk.Label(instructions, text="2. Click 'Refresh All Machines' to download current tool data", font=('Arial', 10)).pack(anchor=tk.W)
        ttk.Label(instructions, text="3. Upload NC file below to see tool availability across all machines", font=('Arial', 10)).pack(anchor=tk.W)
        
        # File upload section
        file_frame = ttk.LabelFrame(self.analysis_frame, text="NC File Analysis", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Label(file_frame, text="NC File:").pack(anchor=tk.W)
        
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(file_select_frame, textvariable=self.file_path_var, width=80).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_select_frame, text="Browse", command=self.browse_nc_file).pack(side=tk.RIGHT, padx=(5,0))
        
        # Action buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="🔄 Refresh All Machines", command=self.refresh_all_machines).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(button_frame, text="🔍 Analyze NC File", command=self.analyze_nc_file).pack(side=tk.LEFT)
        
        # Status/Progress
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(file_frame, textvariable=self.status_var, foreground="blue").pack(anchor=tk.W, pady=5)
        
        self.progress = ttk.Progressbar(file_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
    def setup_machine_tab(self):
        self.machine_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.machine_frame, text="🏭 Machine Management")
        
        # Add machine section
        add_frame = ttk.LabelFrame(self.machine_frame, text="Add New Machine", padding=10)
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
        list_frame = ttk.LabelFrame(self.machine_frame, text="Configured Machines", padding=10)
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
        
    def setup_results_tab(self):
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="📊 Results")
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(self.results_frame, wrap=tk.WORD, font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def load_machine_database(self):
        """Load machine database from JSON file"""
        db_file = Path("machine_database.json")
        if db_file.exists():
            try:
                with open(db_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_machine_database(self):
        """Save machine database to JSON file"""
        with open("machine_database.json", 'w') as f:
            json.dump(self.machine_database, f, indent=2)
    
    def browse_nc_file(self):
        """Browse for NC file"""
        filename = filedialog.askopenfilename(
            title="Select NC File",
            filetypes=[
                ("NC files", "*.nc *.txt *.cnc *.prg *.h"),
                ("Heidenhain files", "*.h"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
    
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
        if machine_id in self.machine_database:
            if not messagebox.askyesno("Confirm", f"Machine {machine_id} already exists. Overwrite?"):
                return
        
        # Add machine
        self.machine_database[machine_id] = {
            'name': self.machine_vars['name'].get().strip(),
            'type': self.machine_vars['type'].get().strip(),
            'location': self.machine_vars['location'].get().strip(),
            'ip_address': self.machine_vars['ip'].get().strip(),
            'tnc_folder': self.machine_vars['tnc_folder'].get().strip(),
            'max_slots': int(self.machine_vars['max_slots'].get() or 130),
            'notes': self.machine_vars['notes'].get().strip(),
            'physical_tools': [],
            'last_updated': None
        }
        
        self.save_machine_database()
        self.refresh_machine_list()
        
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
        
        print(f"Refreshing machine list. Database has {len(self.machine_database)} machines:")
        
        # Add machines
        for machine_id, machine in self.machine_database.items():
            available_count = len(machine.get('physical_tools', []))
            locked_count = len(machine.get('locked_tools', []))
            last_updated = machine.get('last_updated', 'Never')
            
            # Enhanced status with locked tool info
            if available_count > 0:
                if locked_count > 0:
                    status = f'⚠️ {available_count} OK, {locked_count} Locked'
                else:
                    status = f'✅ {available_count} Ready'
            else:
                status = '❌ No Tools'
            
            print(f"Adding machine {machine_id}: {machine.get('name', 'No Name')}")
            
            # Only show locked count if there are actually locked tools
            tool_count_display = str(available_count)
            if locked_count > 0:
                tool_count_display = f"{available_count}+{locked_count}"
            
            item_id = self.machine_tree.insert('', tk.END, values=(
                machine_id,
                machine.get('name', 'Unknown'),
                machine.get('ip_address', 'No IP'),
                tool_count_display,
                last_updated,
                status
            ))
            print(f"Inserted tree item with ID: {item_id}")
        
        print(f"Tree now has {len(self.machine_tree.get_children())} items")
    
    def download_from_machine(self, machine_id):
        """Download TOOL_P.TXT from a specific machine"""
        machine_id = str(machine_id)  # Convert to string to match database keys
        machine = self.machine_database.get(machine_id)
        if not machine:
            return False, "Machine not found"
        
        ip_address = machine['ip_address']
        temp_file = f"temp_{machine_id}_TOOL_P.TXT"
        
        try:
            # Execute TNCCMD command
            cmd = [
                r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                f"-I{ip_address}",
                "Get",
                r"TNC:\TABLE\TOOL_P.TCH",
                temp_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_file):
                # Parse the downloaded file - now returns available and locked tools
                available_tools, locked_tools = self.parse_tool_p_file(temp_file)
                
                # Update machine database
                machine['physical_tools'] = available_tools
                machine['locked_tools'] = locked_tools  # Store locked tools for reporting
                machine['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Clean up temp file
                os.remove(temp_file)
                
                message = f"Available: {len(available_tools)} tools"
                if locked_tools:
                    message += f", Locked/Broken: {len(locked_tools)} tools"
                
                return True, message
            else:
                return False, f"TNCCMD failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def parse_tool_p_file(self, filename):
        """Parse TOOL_P.TXT file - simplified approach like original script"""
        available_tools = []
        locked_tools = []  # Keep this for future use but start with conservative approach
        
        try:
            print(f"\n=== Parsing TOOL_P.TXT file: {filename} ===")
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = 0
                for line in f:
                    line_count += 1
                    columns = line.split()
                    
                    # Debug output for first 10 lines
                    if line_count <= 10:
                        print(f"Line {line_count}: {len(columns)} columns: {columns}")
                    
                    # Same logic as original script - just check for 5+ columns and take tool number
                    if len(columns) >= 5:
                        tool_number = columns[1]  # Tool number from column[1]
                        
                        # Very conservative lock detection - only check for obvious text indicators
                        is_locked = self.check_tool_status_conservative(columns, line)
                        
                        if is_locked:
                            locked_tools.append(tool_number)
                            if line_count <= 10:
                                print(f"  -> Locked tool: {tool_number} ({is_locked})")
                        else:
                            available_tools.append(tool_number)
                            if line_count <= 10:
                                print(f"  -> Available tool: {tool_number}")
            
            print(f"Total lines processed: {line_count}")
            print(f"Available tools: {len(available_tools)}")
            print(f"Locked/Broken tools: {len(locked_tools)}")
            
            # Remove duplicates and sort available tools
            unique_available = list(set(available_tools))
            sorted_available = sorted(unique_available, key=lambda x: int(x) if x.isdigit() else 999999)
            
            # Remove duplicates from locked tools too
            unique_locked = list(set(locked_tools))
            sorted_locked = sorted(unique_locked, key=lambda x: int(x) if x.isdigit() else 999999)
            
            print(f"Final available tools ({len(sorted_available)}): {sorted_available[:20]}...")
            if sorted_locked:
                print(f"Final locked tools ({len(sorted_locked)}): {sorted_locked[:10]}...")
            print("=== Parsing complete ===\n")
            
            return sorted_available, sorted_locked
            
        except Exception as e:
            print(f"ERROR parsing {filename}: {e}")
            return [], []
    
    def check_tool_status_conservative(self, columns, full_line):
        """Very conservative lock detection - only obvious indicators"""
        # Only check for very explicit lock/broken text in the entire line
        line_upper = full_line.upper()
        
        # Only flag as locked if there are very clear text indicators
        obvious_lock_indicators = ['LOCKED', 'BROKEN', 'DISABLED', 'OUT_OF_SERVICE', 'FAULT']
        
        for indicator in obvious_lock_indicators:
            if indicator in line_upper:
                return f"text_indicator_{indicator}"
        
        # Default: assume available (like original script)
        return None
    
    def refresh_all_machines(self):
        """Download tool data from all machines"""
        if not self.machine_database:
            messagebox.showwarning("Warning", "No machines configured. Add machines first.")
            return
        
        self.status_var.set("Downloading tool data from all machines...")
        self.progress.start()
        
        def download_thread():
            success_count = 0
            total_count = len(self.machine_database)
            results = []
            
            for machine_id in self.machine_database:
                self.status_var.set(f"Downloading from {machine_id}...")
                success, message = self.download_from_machine(machine_id)
                
                if success:
                    success_count += 1
                    results.append(f"✅ {machine_id}: {message}")
                else:
                    results.append(f"❌ {machine_id}: {message}")
            
            # Update UI in main thread
            self.root.after(0, lambda: self.download_complete(success_count, total_count, results))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_complete(self, success_count, total_count, results):
        """Called when download is complete"""
        self.progress.stop()
        self.save_machine_database()
        self.refresh_machine_list()
        
        # Show results
        result_text = f"Download Complete: {success_count}/{total_count} machines updated\n\n"
        result_text += "\n".join(results)
        
        self.status_var.set(f"Complete: {success_count}/{total_count} machines updated")
        messagebox.showinfo("Download Complete", result_text)
    
    def test_button(self):
        """Test tree selection functionality"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showinfo("Test", "No machine selected in tree. Please click on a machine first.")
        else:
            try:
                machine_id = self.machine_tree.item(selection[0])['values'][0]
                machine_data = self.machine_database.get(machine_id)
                
                msg = f"Selected machine: {machine_id} (type: {type(machine_id)})\n"
                msg += f"Exists in database: {machine_data is not None}\n\n"
                msg += f"Database contents:\n"
                msg += f"Available keys: {list(self.machine_database.keys())}\n"
                msg += f"Key types: {[type(k) for k in self.machine_database.keys()]}\n\n"
                
                # Try different key formats
                str_key = str(machine_id)
                int_key = int(machine_id) if str(machine_id).isdigit() else None
                
                msg += f"Lookup attempts:\n"
                msg += f"  '{machine_id}': {machine_id in self.machine_database}\n"
                msg += f"  '{str_key}': {str_key in self.machine_database}\n"
                if int_key:
                    msg += f"  {int_key}: {int_key in self.machine_database}\n"
                
                messagebox.showinfo("Debug Results", msg)
            except Exception as e:
                messagebox.showerror("Test Error", f"Error reading selection: {str(e)}")
        
    def download_selected_machine(self):
        """Download tools from selected machine"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine first")
            return
        
        machine_id = str(self.machine_tree.item(selection[0])['values'][0])  # Convert to string
        
        self.status_var.set(f"Downloading from {machine_id}...")
        self.progress.start()
        
        def download_thread():
            success, message = self.download_from_machine(machine_id)
            self.root.after(0, lambda: self.single_download_complete(machine_id, success, message))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def single_download_complete(self, machine_id, success, message):
        """Called when single machine download is complete"""
        self.progress.stop()
        self.save_machine_database()
        self.refresh_machine_list()
        
        if success:
            self.status_var.set(f"{machine_id}: {message}")
            messagebox.showinfo("Success", f"{machine_id}: {message}")
        else:
            self.status_var.set(f"{machine_id}: Failed")
            messagebox.showerror("Error", f"{machine_id}: {message}")
    
    def edit_selected_machine(self):
        """Edit selected machine"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine first")
            return
        
        machine_id = str(self.machine_tree.item(selection[0])['values'][0])  # Convert to string
        machine = self.machine_database[machine_id]
        
        # Populate form with existing data
        self.machine_vars['id'].set(machine_id)
        self.machine_vars['name'].set(machine['name'])
        self.machine_vars['type'].set(machine['type'])
        self.machine_vars['location'].set(machine['location'])
        self.machine_vars['ip'].set(machine['ip_address'])
        self.machine_vars['tnc_folder'].set(machine['tnc_folder'])
        self.machine_vars['max_slots'].set(str(machine['max_slots']))
        self.machine_vars['notes'].set(machine['notes'])
        
        # Switch to machine management tab
        self.notebook.select(1)
    
    def delete_selected_machine(self):
        """Delete selected machine"""
        selection = self.machine_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a machine first")
            return
        
        machine_id = str(self.machine_tree.item(selection[0])['values'][0])  # Convert to string
        
        if messagebox.askyesno("Confirm Delete", f"Delete machine {machine_id}?"):
            del self.machine_database[machine_id]
            self.save_machine_database()
            self.refresh_machine_list()
            messagebox.showinfo("Success", f"Machine {machine_id} deleted")
    
    def analyze_nc_file(self):
        """Analyze the uploaded NC file with automatic tool data refresh"""
        nc_file = self.file_path_var.get()
        if not nc_file or not os.path.exists(nc_file):
            messagebox.showerror("Error", "Please select a valid NC file")
            return
        
        if not self.machine_database:
            messagebox.showwarning("Warning", "No machines configured")
            return
        
        # Ask user if they want to refresh tool data first
        refresh_tools = messagebox.askyesno(
            "Refresh Tool Data",
            "Download fresh tool data from all machines before analysis?\n\n" +
            "This ensures the most current tool availability.\n\n" +
            "Click 'Yes' for fresh data (recommended)\n" +
            "Click 'No' to use existing data"
        )
        
        self.progress.start()
        
        def analyze_with_refresh_thread():
            try:
                success_count = 0
                total_machines = len(self.machine_database)
                
                if refresh_tools:
                    # Step 1: Download tool data from all machines
                    self.status_var.set("Downloading fresh tool data from all machines...")
                    
                    for i, machine_id in enumerate(self.machine_database.keys(), 1):
                        self.status_var.set(f"Downloading from {machine_id} ({i}/{total_machines})...")
                        success, message = self.download_from_machine(machine_id)
                        if success:
                            success_count += 1
                    
                    self.save_machine_database()
                    self.root.after(0, self.refresh_machine_list)
                    
                    print(f"Tool download complete: {success_count}/{total_machines} machines updated")
                
                # Step 2: Analyze NC file
                self.status_var.set("Analyzing NC file with current tool data...")
                analysis = self.perform_nc_analysis(nc_file)
                
                # Add download info to analysis
                if refresh_tools:
                    analysis['download_info'] = f"Tool data refreshed from {success_count}/{total_machines} machines"
                else:
                    analysis['download_info'] = "Using existing tool data (not refreshed)"
                
                self.root.after(0, lambda: self.analysis_complete(analysis))
                
            except Exception as e:
                self.root.after(0, lambda: self.analysis_error(str(e)))
        
        threading.Thread(target=analyze_with_refresh_thread, daemon=True).start()
    
    def perform_nc_analysis(self, nc_file):
        """Perform the actual NC file analysis"""
        # Parse NC file for tool calls
        tool_numbers = []
        blk_form_data = []
        cutter_comp_info = {}
        preset_values = []
        f_value_errors = []
        
        with open(nc_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        current_tool_number = None
        
        for i, line in enumerate(lines, 1):
            # Check for TOOL CALL
            tool_call_match = re.search(r'TOOL CALL (\d+)', line)
            if tool_call_match:
                current_tool_number = tool_call_match.group(1)
                if current_tool_number not in tool_numbers:
                    tool_numbers.append(current_tool_number)
                    print(f"NC File - Found tool call: {current_tool_number} (type: {type(current_tool_number)})")
                
                # Initialize cutter comp as off
                cutter_comp_info[current_tool_number] = 'Cutter Comp: Off'
                
                # Look for RR/RL in subsequent lines
                for subsequent_line in lines[i:]:
                    if re.search(r'TOOL CALL (\d+)', subsequent_line):
                        break
                    if ' RR' in subsequent_line or ' RL' in subsequent_line:
                        cutter_comp_info[current_tool_number] = 'Cutter Comp: On'
                        break
            
            # Check for BLK FORM
            blk_form_match = re.search(r'BLK FORM \d+\.?\d* (?:Z )?X([-+]?\d+\.?\d*) Y([-+]?\d+\.?\d*) Z([-+]?\d+\.?\d*)', line)
            if blk_form_match:
                blk_form_data.append({
                    'x': float(blk_form_match.group(1)),
                    'y': float(blk_form_match.group(2)),
                    'z': float(blk_form_match.group(3))
                })
            
            # Check for Q339 (preset values)
            q339_match = re.search(r'Q339=([-+]?\d+\.?\d*)', line)
            if q339_match:
                preset_values.append(float(q339_match.group(1)))
            
            # Check F values
            f_matches = re.findall(r'F(\d+(?:\.\d*)?)', line)
            for f_value_str in f_matches:
                try:
                    f_value = float(f_value_str)
                    if f_value > 80000:
                        f_value_errors.append({
                            'line': i,
                            'value': f_value,
                            'text': line.strip()
                        })
                except ValueError:
                    pass
        
        # Calculate stock dimensions
        dimensions = None
        if len(blk_form_data) >= 2:
            width = abs(blk_form_data[1]['x'] - blk_form_data[0]['x'])
            height = abs(blk_form_data[1]['y'] - blk_form_data[0]['y'])
            depth = abs(blk_form_data[1]['z'] - blk_form_data[0]['z'])
            dimensions = {'width': width, 'height': height, 'depth': depth}
        
        # Analyze machine compatibility with GUI debugging
        machine_analysis = []
        debug_info = []
        
        debug_info.append("=== DEBUGGING TOOL COMPARISON ===")
        debug_info.append(f"Required tools from NC file: {tool_numbers}")
        debug_info.append(f"Required tools types: {[type(t).__name__ for t in tool_numbers[:5]]}")
        debug_info.append("")
        
        for machine_id, machine in self.machine_database.items():
            debug_info.append(f"--- Machine {machine_id} ---")
            physical_tools = machine.get('physical_tools', [])
            locked_tools = machine.get('locked_tools', [])
            debug_info.append(f"Physical tools: {physical_tools[:10]}...")
            debug_info.append(f"Physical tools types: {[type(t).__name__ for t in physical_tools[:5]]}")
            debug_info.append(f"Total physical tools: {len(physical_tools)}")
            debug_info.append(f"Total locked tools: {len(locked_tools)}")
            
            # Check each required tool individually
            matching_tools = []
            missing_tools = []
            locked_required_tools = []
            
            for tool in tool_numbers:
                if tool in physical_tools:
                    matching_tools.append(tool)
                    debug_info.append(f"  ✅ Tool {tool}: FOUND")
                elif tool in locked_tools:
                    locked_required_tools.append(tool)
                    debug_info.append(f"  🔒 Tool {tool}: LOCKED/BROKEN")
                else:
                    missing_tools.append(tool)
                    debug_info.append(f"  ❌ Tool {tool}: MISSING")
                    
                    # Check if it exists as different type
                    str_tool = str(tool)
                    int_tool = int(tool) if str(tool).isdigit() else None
                    if str_tool in physical_tools:
                        debug_info.append(f"    🔍 But '{str_tool}' (str) exists!")
                        # Fix the mismatch by adding to matching
                        matching_tools.append(tool)
                        missing_tools.remove(tool)
                    elif int_tool and int_tool in physical_tools:
                        debug_info.append(f"    🔍 But {int_tool} (int) exists!")
                        # Fix the mismatch by adding to matching
                        matching_tools.append(tool)
                        missing_tools.remove(tool)
                    elif str_tool in locked_tools:
                        debug_info.append(f"    🔒 But '{str_tool}' (str) is locked!")
                        locked_required_tools.append(tool)
                        missing_tools.remove(tool)
                    elif int_tool and int_tool in locked_tools:
                        debug_info.append(f"    🔒 But {int_tool} (int) is locked!")
                        locked_required_tools.append(tool)
                        missing_tools.remove(tool)
            
            match_percentage = (len(matching_tools) / len(tool_numbers) * 100) if tool_numbers else 0
            debug_info.append(f"Result: {len(matching_tools)}/{len(tool_numbers)} = {match_percentage:.1f}%")
            if locked_required_tools:
                debug_info.append(f"Locked required tools: {len(locked_required_tools)}")
            debug_info.append("")
            
            machine_analysis.append({
                'machine_id': machine_id,
                'machine_name': machine['name'],
                'machine_type': machine['type'],
                'location': machine['location'],
                'matching_tools': matching_tools,
                'missing_tools': missing_tools,
                'locked_required_tools': locked_required_tools,
                'match_percentage': round(match_percentage),
                'total_physical_tools': len(physical_tools),
                'total_locked_tools': len(locked_tools),
                'last_updated': machine.get('last_updated', 'Never')
            })
        
        # Sort by match percentage
        machine_analysis.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return {
            'file_name': os.path.basename(nc_file),
            'tool_numbers': sorted(tool_numbers, key=int),
            'cutter_comp_info': cutter_comp_info,
            'preset_values': preset_values,
            'f_value_errors': f_value_errors,
            'dimensions': dimensions,
            'total_tools': len(tool_numbers),
            'machine_analysis': machine_analysis,
            'debug_info': debug_info  # Add debug info to results
        }
    
    def analysis_complete(self, analysis):
        """Called when NC analysis is complete"""
        self.progress.stop()
        self.current_nc_analysis = analysis
        self.status_var.set(f"Analysis complete: {analysis['total_tools']} tools required")
        
        # Display results
        self.display_results(analysis)
        
        # Switch to results tab
        self.notebook.select(2)
    
    def analysis_error(self, error_msg):
        """Called when NC analysis fails"""
        self.progress.stop()
        self.status_var.set("Analysis failed")
        messagebox.showerror("Analysis Error", f"Failed to analyze NC file:\n{error_msg}")
    
    def display_results(self, analysis):
        """Display analysis results"""
        self.results_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 60)
        output.append(f"NC TOOL ANALYSIS RESULTS")
        output.append("=" * 60)
        output.append(f"File: {analysis['file_name']}")
        output.append(f"Tools Required: {analysis['total_tools']}")
        output.append(f"F-Value Errors: {len(analysis['f_value_errors'])}")
        
        # Add download info if available
        if 'download_info' in analysis:
            output.append(f"Tool Data: {analysis['download_info']}")
        
        output.append("")
        
        # Add debug information at the top
        if 'debug_info' in analysis:
            output.extend(analysis['debug_info'])
            output.append("")
            output.append("=" * 60)
            output.append("")
        
        # Stock dimensions
        if analysis['dimensions']:
            dim = analysis['dimensions']
            output.append("STOCK DIMENSIONS:")
            output.append(f"Width: {dim['width']:.2f} mm")
            output.append(f"Height: {dim['height']:.2f} mm") 
            output.append(f"Depth: {dim['depth']:.2f} mm")
            output.append("")
        
        # Preset values
        if analysis['preset_values']:
            output.append("PRESET VALUES:")
            for preset in analysis['preset_values']:
                output.append(f"Preset: {preset}")
            output.append("")
        
        # Tools needed
        output.append("TOOLS NEEDED IN SEQUENCE ORDER:")
        output.append("-" * 40)
        for tool in analysis['tool_numbers']:
            comp_info = analysis['cutter_comp_info'].get(tool, 'Cutter Comp: Off')
            output.append(f"T{tool}")
            output.append(f"{comp_info}")
            output.append("-" * 20)
        output.append("")
        
        # Machine analysis
        output.append("MACHINE COMPATIBILITY ANALYSIS:")
        output.append("=" * 40)
        
        for machine in analysis['machine_analysis']:
            output.append(f"\n{machine['machine_name']} ({machine['machine_id']})")
            output.append(f"Type: {machine['machine_type']}")
            output.append(f"Location: {machine['location']}")
            output.append(f"Match: {machine['match_percentage']}% ({len(machine['matching_tools'])}/{analysis['total_tools']} tools)")
            
            # Enhanced tool status display
            available_count = machine['total_physical_tools']
            locked_count = machine.get('total_locked_tools', 0)
            if locked_count > 0:
                output.append(f"Tool Status: {available_count} Available, {locked_count} Locked/Broken")
            else:
                output.append(f"Physical Tools Available: {available_count}")
            
            output.append(f"Last Updated: {machine['last_updated']}")
            
            # Show tool status for required tools
            if machine['missing_tools']:
                output.append(f"❌ Missing Tools: T{', T'.join(machine['missing_tools'])}")
            
            locked_required = machine.get('locked_required_tools', [])
            if locked_required:
                output.append(f"🔒 Required Tools Locked/Broken: T{', T'.join(locked_required)}")
            
            if not machine['missing_tools'] and not locked_required:
                output.append("✅ All required tools are available!")
            elif not machine['missing_tools'] and locked_required:
                output.append("⚠️ All tools physically present but some are locked/broken!")
            
            output.append("-" * 40)
        
        # F-value errors
        if analysis['f_value_errors']:
            output.append("\nF-VALUE ERRORS (>80000):")
            for error in analysis['f_value_errors']:
                output.append(f"Line {error['line']}: F{error['value']} - {error['text']}")
        
        self.results_text.insert(tk.END, "\n".join(output))

def main():
    root = tk.Tk()
    app = NCToolAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()