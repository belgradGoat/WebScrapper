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
import math
from pathlib import Path
from datetime import datetime

class NCCycleTimeCalculator:
    """Calculate cycle time from NC code by analyzing movements and feedrates"""
    
    def __init__(self):
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        self.current_feedrate = 0  # mm/min
        self.rapid_feedrate = 10000  # Default rapid feedrate (mm/min)
        self.tool_change_time = 10  # Default tool change time (seconds)
        self.total_time = 0  # Total time in seconds
        self.current_tool = None
        self.movements = []
        self.operation_times = {
            'rapid': 0,
            'feed': 0,
            'tool_change': 0,
            'dwell': 0,
            'other': 0
        }
        self.operation_counts = {
            'rapid': 0,
            'feed': 0,
            'tool_change': 0,
            'dwell': 0,
            'other': 0
        }
        
    def parse_nc_file(self, file_path):
        """Parse NC file and calculate cycle time"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        line_number = 0
        for line in lines:
            line_number += 1
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith(';') or line.startswith('(') or line.startswith('*'):
                continue
                
            # Process the line
            self.process_line(line, line_number)
            
        return {
            'total_time': self.total_time,
            'total_time_formatted': self.format_time(self.total_time),
            'operation_times': self.operation_times,
            'operation_counts': self.operation_counts,
            'movements': self.movements
        }
    
    def process_line(self, line, line_number):
        """Process a single line of Heidenhain NC code"""
        # Tool change
        tool_match = re.search(r'TOOL CALL (\d+)', line)
        if tool_match:
            new_tool = tool_match.group(1)
            if self.current_tool != new_tool:
                self.current_tool = new_tool
                self.add_time('tool_change', self.tool_change_time)
                self.operation_counts['tool_change'] += 1
                self.movements.append({
                    'line': line_number,
                    'type': 'tool_change',
                    'tool': self.current_tool,
                    'time': self.tool_change_time
                })
            return
            
        # Feedrate
        f_match = re.search(r'F(\d+\.?\d*)', line)
        if f_match:
            self.current_feedrate = float(f_match.group(1))
        
        # FMAX (rapid movement)
        is_rapid = 'FMAX' in line
        
        # Dwell
        dwell_match = re.search(r'DWELL\s+[F](\d+\.?\d*)', line)
        if dwell_match:
            dwell_time = float(dwell_match.group(1))
            self.add_time('dwell', dwell_time)
            self.operation_counts['dwell'] += 1
            self.movements.append({
                'line': line_number,
                'type': 'dwell',
                'time': dwell_time
            })
            return
            
        # Movement commands (L, C, CR, CT)
        new_position = self.current_position.copy()
        has_movement = False
        
        # Extract X, Y, Z coordinates
        for axis in ['X', 'Y', 'Z']:
            axis_match = re.search(rf'{axis}([+-]?\d+\.?\d*)', line)
            if axis_match:
                new_position[axis] = float(axis_match.group(1))
                has_movement = True
                
        if has_movement:
            # Calculate distance
            distance = self.calculate_distance(self.current_position, new_position)
            
            # Calculate time
            if is_rapid:
                time_seconds = (distance / self.rapid_feedrate) * 60
                movement_type = 'rapid'
            else:
                if self.current_feedrate <= 0:
                    # Default feedrate if none specified
                    self.current_feedrate = 100
                time_seconds = (distance / self.current_feedrate) * 60
                movement_type = 'feed'
                
            self.add_time(movement_type, time_seconds)
            self.operation_counts[movement_type] += 1
            
            self.movements.append({
                'line': line_number,
                'type': movement_type,
                'from': self.current_position.copy(),
                'to': new_position.copy(),
                'distance': distance,
                'feedrate': self.rapid_feedrate if is_rapid else self.current_feedrate,
                'time': time_seconds
            })
            
            # Update current position
            self.current_position = new_position
    
    def calculate_distance(self, pos1, pos2):
        """Calculate 3D distance between two points"""
        return math.sqrt(
            (pos2['X'] - pos1['X'])**2 +
            (pos2['Y'] - pos1['Y'])**2 +
            (pos2['Z'] - pos1['Z'])**2
        )
    
    def add_time(self, operation_type, seconds):
        """Add time to total and operation-specific counters"""
        self.total_time += seconds
        self.operation_times[operation_type] += seconds
    
    def format_time(self, seconds):
        """Format time in seconds to hours:minutes:seconds"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

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
        ttk.Button(button_frame, text="🔍 Analyze NC File", command=self.analyze_nc_file).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(button_frame, text="⏱️ Calculate Cycle Time", command=self.calculate_cycle_time).pack(side=tk.LEFT)
        
        # Status/Progress
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(file_frame, textvariable=self.status_var, foreground="blue").pack(anchor=tk.W, pady=5)
        
        self.progress = ttk.Progressbar(file_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Quick Results Summary with Machine Cards
        summary_frame = ttk.LabelFrame(self.analysis_frame, text="Machine Compatibility Summary", padding=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollable frame for machine cards
        summary_canvas = tk.Canvas(summary_frame)
        summary_scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=summary_canvas.yview)
        self.summary_scrollable_frame = ttk.Frame(summary_canvas)
        
        self.summary_scrollable_frame.bind(
            "<Configure>",
            lambda e: summary_canvas.configure(scrollregion=summary_canvas.bbox("all"))
        )
        
        summary_canvas.create_window((0, 0), window=self.summary_scrollable_frame, anchor="nw")
        summary_canvas.configure(yscrollcommand=summary_scrollbar.set)
        
        summary_canvas.pack(side="left", fill="both", expand=True)
        summary_scrollbar.pack(side="right", fill="y")
        
        # Initial message
        initial_msg = ttk.Label(self.summary_scrollable_frame,
                               text="Upload an NC file and click 'Analyze NC File' to see machine compatibility cards here.\n\n" +
                                    "Each machine will show:\n" +
                                    "• Tool availability status and count\n" +
                                    "• Send to Machine button for direct file transfer\n" +
                                    "• Tool life warnings for critical tools\n" +
                                    "• Missing/locked tool information",
                               font=('Arial', 10), justify=tk.LEFT)
        initial_msg.pack(padx=20, pady=20)
        
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
            # Step 1: Download TOOL_P.TCH for tool availability
            cmd = [
                r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                f"-I{ip_address}",
                "Get",
                r"TNC:\TABLE\TOOL_P.TCH",
                temp_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(temp_file):
                # Parse the downloaded file for tool availability
                available_tools, locked_tools, _ = self.parse_tool_p_file(temp_file)
                os.remove(temp_file)  # Clean up temp file
                
                # Step 2: Download tool.t for tool life data
                tool_t_file = f"temp_{machine_id}_tool.t"
                cmd_tool_t = [
                    r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                    f"-I{ip_address}",
                    "Get",
                    r"TNC:\TABLE\tool.t",
                    tool_t_file
                ]
                
                result_tool_t = subprocess.run(cmd_tool_t, capture_output=True, text=True, timeout=30)
                tool_life_data = {}
                
                if result_tool_t.returncode == 0 and os.path.exists(tool_t_file):
                    # Parse tool.t for tool life data using v3 script logic
                    tool_life_data = self.parse_tool_t_file(tool_t_file, available_tools)
                    os.remove(tool_t_file)  # Clean up temp file
                
                # Update machine database
                machine['physical_tools'] = available_tools
                machine['locked_tools'] = locked_tools
                machine['tool_life_data'] = tool_life_data
                machine['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                message = f"Available: {len(available_tools)} tools"
                if locked_tools:
                    message += f", Locked/Broken: {len(locked_tools)} tools"
                if tool_life_data:
                    message += f", Life data: {len(tool_life_data)} tools"
                
                return True, message
            else:
                return False, f"TNCCMD failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Connection timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def parse_tool_p_file(self, filename):
        """Parse TOOL_P.TXT file - extract tool availability only (tool life comes from tool.t)"""
        available_tools = []
        locked_tools = []
        
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
            
            # Remove duplicates and sort tools
            unique_available = list(set(available_tools))
            sorted_available = sorted(unique_available, key=lambda x: int(x) if x.isdigit() else 999999)
            
            unique_locked = list(set(locked_tools))
            sorted_locked = sorted(unique_locked, key=lambda x: int(x) if x.isdigit() else 999999)
            
            print(f"Final available tools ({len(sorted_available)}): {sorted_available[:20]}...")
            if sorted_locked:
                print(f"Final locked tools ({len(sorted_locked)}): {sorted_locked[:10]}...")
            print("=== TOOL_P.TXT parsing complete ===\n")
            
            return sorted_available, sorted_locked, {}  # Empty dict for compatibility
            
        except Exception as e:
            print(f"ERROR parsing {filename}: {e}")
            return [], [], {}
    
    def extract_tool_life(self, columns, tool_number, debug=False):
        """Extract tool life data from TOOL_P.TXT columns based on typical Heidenhain format"""
        tool_life_info = {}
        
        try:
            if debug:
                print(f"  Analyzing tool life for T{tool_number}:")
                # Show all numeric values with their positions
                numeric_candidates = []
                for i, col in enumerate(columns):
                    try:
                        val = float(col)
                        numeric_candidates.append((i, val))
                    except ValueError:
                        pass
                print(f"    All numeric values: {numeric_candidates}")
            
            current_time = None
            max_time = None
            current_col = None
            max_col = None
            
            # Strategy: Find all reasonable tool life candidates and pick the best pair
            candidates = []
            for i in range(2, len(columns)):  # Skip slot and tool number
                try:
                    val = float(columns[i])
                    # Tool life is typically 0-50000 minutes, but could be higher
                    # Exclude obvious non-tool-life values like 0, very small decimals, etc.
                    if 0.1 <= val <= 100000:  # Broader range, exclude exact zeros
                        candidates.append((i, val))
                except (ValueError, IndexError):
                    continue
            
            if debug:
                print(f"    Tool life candidates (0.1-100000): {candidates}")
            
            # Find current and max tool life
            if len(candidates) >= 2:
                # Look for pairs where one is smaller (current) and one is larger (max)
                candidates.sort(key=lambda x: x[1])  # Sort by value
                
                # Take first non-zero value as current, find a larger one as max
                for i, (col_idx, val) in enumerate(candidates):
                    if current_time is None and val > 0:
                        current_time = val
                        current_col = col_idx
                        # Look for a larger value as max time
                        for j in range(i+1, len(candidates)):
                            max_col_idx, max_val = candidates[j]
                            if max_val > current_time:
                                max_time = max_val
                                max_col = max_col_idx
                                break
                        break
            elif len(candidates) == 1:
                # Only one candidate - use as current time
                current_col, current_time = candidates[0]
            
            # Store results if we found anything
            if current_time is not None:
                tool_life_info['current_time'] = current_time
                tool_life_info['current_col'] = current_col
                
                if max_time is not None and max_time > 0:
                    tool_life_info['max_time'] = max_time
                    tool_life_info['max_col'] = max_col
                    tool_life_info['usage_percentage'] = (current_time / max_time) * 100
                else:
                    tool_life_info['max_time'] = None
                    tool_life_info['max_col'] = None
                    tool_life_info['usage_percentage'] = None
                
                if debug:
                    percentage_str = f"{tool_life_info.get('usage_percentage', 0):.1f}%" if tool_life_info.get('usage_percentage') is not None else "N/A"
                    print(f"    -> SELECTED: Current={current_time:.1f} (col[{current_col}]), Max={max_time or 'N/A'} (col[{max_col}]), Usage={percentage_str}")
                
                return tool_life_info
            elif debug:
                print(f"    -> No suitable tool life values found")
        
        except Exception as e:
            if debug:
                print(f"    Tool life extraction error: {e}")
        
        return None
    
    def parse_tool_t_file(self, filename, available_tools):
        """Parse tool.t file for tool life data using v3 script logic"""
        tool_life_data = {}
        
        try:
            print(f"\n=== Parsing tool.t file: {filename} ===")
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Find CUR.TIME or CUR_TIME header (like v3 script)
            cur_time_column = None
            cur_time_index = None
            
            for idx, line in enumerate(lines):
                if 'CUR.TIME' in line:
                    cur_time_index = idx
                    cur_time_column = line.index('CUR.TIME')
                    print(f"Found CUR.TIME header at line {idx}, column position {cur_time_column}")
                    break
                elif 'CUR_TIME' in line:
                    cur_time_index = idx
                    cur_time_column = line.index('CUR_TIME')
                    print(f"Found CUR_TIME header at line {idx}, column position {cur_time_column}")
                    break
            
            if cur_time_column is None or cur_time_index is None:
                print("CUR.TIME or CUR_TIME header not found in tool.t")
                return {}
            
            # Parse tool life data (skip 2 lines after header like v3 script)
            for i, cur_time_line in enumerate(lines[cur_time_index + 2:]):
                tool_number = str(i + 1)  # Tool numbers start from 1
                
                # Only process tools that are available
                if tool_number in available_tools:
                    try:
                        # Extract current time value from the column position
                        cur_time_value_str = cur_time_line[cur_time_column:].strip().split()[0]
                        cur_time_value = float(cur_time_value_str)
                        
                        if cur_time_value > 0:
                            tool_life_data[tool_number] = {
                                'current_time': cur_time_value,
                                'max_time': None,  # tool.t doesn't contain max time
                                'usage_percentage': None
                            }
                            print(f"Tool {tool_number}: Current time = {cur_time_value} minutes")
                        
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing tool {tool_number}: {e}")
                        continue
            
            print(f"Extracted tool life data for {len(tool_life_data)} tools")
            print("=== tool.t parsing complete ===\n")
            
            return tool_life_data
            
        except Exception as e:
            print(f"ERROR parsing {filename}: {e}")
            return {}
    
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
        
        # Display summary in Analysis tab
        self.display_summary(analysis)
        
        # Display detailed results in Results tab
        self.display_results(analysis)
        
        # Keep user on Analysis tab to see summary
        # They can switch to Results tab for detailed info
    
    def analysis_error(self, error_msg):
        """Called when NC analysis fails"""
        self.progress.stop()
        self.status_var.set("Analysis failed")
        messagebox.showerror("Analysis Error", f"Failed to analyze NC file:\n{error_msg}")
    
    def display_summary(self, analysis):
        """Display machine cards in Analysis tab"""
        # Clear existing widgets
        for widget in self.summary_scrollable_frame.winfo_children():
            widget.destroy()
        
        # File info header
        header_frame = ttk.Frame(self.summary_scrollable_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text=f"📄 File: {analysis['file_name']}", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"🔧 Tools Required: {analysis['total_tools']}", font=('Arial', 10)).pack(anchor=tk.W)
        
        if 'download_info' in analysis:
            ttk.Label(header_frame, text=f"📊 {analysis['download_info']}", font=('Arial', 10)).pack(anchor=tk.W)
        
        ttk.Separator(self.summary_scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=10)
        
        # Create machine cards (ranked by compatibility)
        for i, machine in enumerate(analysis['machine_analysis'], 1):
            self.create_machine_card(machine, analysis, i)
        
        # Footer note
        footer_frame = ttk.Frame(self.summary_scrollable_frame)
        footer_frame.pack(fill=tk.X, padx=10, pady=20)
        
        footer_text = ttk.Label(footer_frame,
                               text="💡 Switch to 'Results' tab for detailed analysis including tool sequences, dimensions, and debug info",
                               font=('Arial', 9), foreground='blue')
        footer_text.pack(anchor=tk.W)
    
    def create_machine_card(self, machine, analysis, rank):
        """Create individual machine card like HTML version"""
        available_tools = len(machine['matching_tools'])
        total_required = analysis['total_tools']
        missing_count = len(machine['missing_tools'])
        locked_count = len(machine.get('locked_required_tools', []))
        
        # Determine card color based on match level
        if machine['match_percentage'] == 100:
            card_color = '#d4edda'  # Green
            border_color = '#28a745'
        elif machine['match_percentage'] >= 80:
            card_color = '#fff3cd'  # Yellow
            border_color = '#ffc107'
        else:
            card_color = '#f8d7da'  # Red
            border_color = '#dc3545'
        
        # Main card frame
        card_frame = tk.Frame(self.summary_scrollable_frame, bg=card_color, relief=tk.RAISED, bd=2)
        card_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Configure border color (using a thin frame)
        border_frame = tk.Frame(card_frame, bg=border_color, height=4)
        border_frame.pack(fill=tk.X)
        
        # Card content
        content_frame = tk.Frame(card_frame, bg=card_color)
        content_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Header with rank and match percentage
        header_frame = tk.Frame(content_frame, bg=card_color)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        rank_label = tk.Label(header_frame, text=f"#{rank}", font=('Arial', 16, 'bold'), bg=card_color)
        rank_label.pack(side=tk.LEFT)
        
        match_text = f"{machine['match_percentage']}% Match" if machine['match_percentage'] > 0 else "No Tools Available"
        match_label = tk.Label(header_frame, text=match_text, font=('Arial', 14, 'bold'), bg=card_color)
        match_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Machine info
        info_frame = tk.Frame(content_frame, bg=card_color)
        info_frame.pack(fill=tk.X, pady=5)
        
        machine_name = tk.Label(info_frame, text=f"🏭 {machine['machine_name']} ({machine['machine_id']})",
                               font=('Arial', 12, 'bold'), bg=card_color)
        machine_name.pack(anchor=tk.W)
        
        location_label = tk.Label(info_frame, text=f"📍 {machine['location']}", font=('Arial', 10), bg=card_color)
        location_label.pack(anchor=tk.W)
        
        tools_label = tk.Label(info_frame, text=f"🔧 Tools: {available_tools}/{total_required} available",
                              font=('Arial', 10), bg=card_color)
        tools_label.pack(anchor=tk.W)
        
        # Status and issues
        status_frame = tk.Frame(content_frame, bg=card_color)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Show missing tools if any
        if missing_count > 0:
            missing_tools = machine['missing_tools'][:3]
            missing_text = f"❌ Missing: T{', T'.join(missing_tools)}"
            if len(machine['missing_tools']) > 3:
                missing_text += f" (+{len(machine['missing_tools']) - 3} more)"
            missing_label = tk.Label(status_frame, text=missing_text, font=('Arial', 9), bg=card_color, fg='red')
            missing_label.pack(anchor=tk.W)
        
        # Show locked tools if any
        if locked_count > 0:
            locked_tools = machine.get('locked_required_tools', [])[:3]
            locked_text = f"🔒 Locked: T{', T'.join(locked_tools)}"
            if len(machine.get('locked_required_tools', [])) > 3:
                locked_text += f" (+{len(machine.get('locked_required_tools', [])) - 3} more)"
            locked_label = tk.Label(status_frame, text=locked_text, font=('Arial', 9), bg=card_color, fg='orange')
            locked_label.pack(anchor=tk.W)
        
        # Tool life warnings
        machine_data = self.machine_database.get(machine['machine_id'], {})
        tool_life_data = machine_data.get('tool_life_data', {})
        critical_tools = []
        
        for tool in machine['matching_tools']:
            if tool in tool_life_data:
                life_info = tool_life_data[tool]
                current_time = life_info.get('current_time', 0)
                if current_time > 60:  # High usage threshold
                    critical_tools.append(f"T{tool}({current_time:.0f}min)")
        
        if critical_tools:
            life_text = f"⏰ High Usage: {', '.join(critical_tools[:3])}"
            if len(critical_tools) > 3:
                life_text += f" (+{len(critical_tools) - 3} more)"
            life_label = tk.Label(status_frame, text=life_text, font=('Arial', 9), bg=card_color, fg='purple')
            life_label.pack(anchor=tk.W)
        
        # Action buttons
        button_frame = tk.Frame(content_frame, bg=card_color)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Send to Machine button
        send_btn = ttk.Button(button_frame, text="📤 Send to Machine",
                             command=lambda m=machine: self.send_to_machine(m, analysis['file_name']))
        send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # View Details button
        details_btn = ttk.Button(button_frame, text="📋 View Details",
                                command=lambda: self.notebook.select(2))  # Switch to Results tab
        details_btn.pack(side=tk.LEFT)
        
        # Ready indicator
        if missing_count == 0 and locked_count == 0:
            ready_label = tk.Label(button_frame, text="✅ READY TO RUN", font=('Arial', 10, 'bold'),
                                  bg=card_color, fg='green')
            ready_label.pack(side=tk.RIGHT)
        elif missing_count == 0:
            warning_label = tk.Label(button_frame, text="⚠️ CHECK LOCKED TOOLS", font=('Arial', 10, 'bold'),
                                   bg=card_color, fg='orange')
            warning_label.pack(side=tk.RIGHT)
    
    def send_to_machine(self, machine, filename):
        """Send NC file to machine using TNCCMD"""
        if not hasattr(self, 'current_nc_analysis') or not self.current_nc_analysis:
            messagebox.showerror("Error", "No NC file analysis available")
            return
        
        # Get the original NC file path
        nc_file_path = self.file_path_var.get()
        if not nc_file_path or not os.path.exists(nc_file_path):
            messagebox.showerror("Error", "Original NC file not found. Please select the NC file again.")
            return
        
        machine_data = self.machine_database.get(machine['machine_id'])
        if not machine_data:
            messagebox.showerror("Error", "Machine data not found")
            return
        
        ip_address = machine_data.get('ip_address')
        tnc_folder = machine_data.get('tnc_folder', '')
        
        if not ip_address:
            messagebox.showerror("Error", f"IP address not configured for {machine['machine_name']}")
            return
        
        # Confirm the transfer
        result = messagebox.askyesno(
            "Send File to Machine",
            f"Send '{filename}' to {machine['machine_name']}?\n\n" +
            f"Machine: {machine['machine_name']} ({machine['machine_id']})\n" +
            f"IP Address: {ip_address}\n" +
            f"TNC Folder: {tnc_folder or 'Root'}\n" +
            f"Match: {machine['match_percentage']}% ({len(machine['matching_tools'])}/{self.current_nc_analysis['total_tools']} tools)\n\n" +
            "The file will be uploaded to the machine's TNC folder."
        )
        
        if not result:
            return
        
        # Show progress
        self.status_var.set(f"Sending {filename} to {machine['machine_name']}...")
        self.progress.start()
        
        def send_file_thread():
            try:
                # Construct remote path
                remote_path = f"TNC:\\{tnc_folder}\\{filename}" if tnc_folder else f"TNC:\\{filename}"
                
                # TNCCMD Put command
                cmd = [
                    r"C:\Program Files (x86)\HEIDENHAIN\TNCremo\TNCCMD.exe",
                    f"-I{ip_address}",
                    "Put",
                    nc_file_path,
                    remote_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    self.root.after(0, lambda: self.send_complete(True, machine['machine_name'], filename, None))
                else:
                    error_message = result.stderr or "Unknown error"
                    self.root.after(0, lambda: self.send_complete(False, machine['machine_name'], filename, error_message))
                    
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self.send_complete(False, machine['machine_name'], filename, "Connection timeout"))
            except Exception as e:
                self.root.after(0, lambda: self.send_complete(False, machine['machine_name'], filename, str(e)))
        
        threading.Thread(target=send_file_thread, daemon=True).start()
    
    def send_complete(self, success, machine_name, filename, error_message):
        """Called when file send is complete"""
        self.progress.stop()
        
        if success:
            self.status_var.set(f"✅ {filename} sent to {machine_name}")
            messagebox.showinfo("Success", f"File '{filename}' successfully sent to {machine_name}!")
        else:
            self.status_var.set(f"❌ Failed to send to {machine_name}")
            messagebox.showerror("Send Failed",
                               f"Failed to send '{filename}' to {machine_name}.\n\n" +
                               f"Error: {error_message}\n\n" +
                               "Please check:\n" +
                               "• Machine IP address is correct\n" +
                               "• Machine is powered on and connected\n" +
                               "• TNCremo is installed correctly\n" +
                               "• TNC folder path is valid")

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
        
        # Tools needed with life information
        output.append("TOOLS NEEDED IN SEQUENCE ORDER:")
        output.append("-" * 40)
        for tool in analysis['tool_numbers']:
            comp_info = analysis['cutter_comp_info'].get(tool, 'Cutter Comp: Off')
            output.append(f"T{tool}")
            output.append(f"{comp_info}")
            
            # Add tool life information if available from any machine
            tool_life_found = False
            for machine in analysis['machine_analysis']:
                machine_data = self.machine_database.get(machine['machine_id'], {})
                tool_life_data = machine_data.get('tool_life_data', {})
                if tool in tool_life_data:
                    life_info = tool_life_data[tool]
                    current = life_info.get('current_time', 0)
                    max_time = life_info.get('max_time')
                    percentage = life_info.get('usage_percentage')
                    
                    if max_time is not None and percentage is not None:
                        output.append(f"Tool Life: {current:.1f}/{max_time:.1f} min ({percentage:.1f}% used) - {machine['machine_id']}")
                    else:
                        output.append(f"Tool Life: {current:.1f} min used - {machine['machine_id']}")
                    tool_life_found = True
                    break
            
            if not tool_life_found:
                output.append("Tool Life: No data available")
            
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
            
            # Show tool life information for available required tools
            machine_data = self.machine_database.get(machine['machine_id'], {})
            tool_life_data = machine_data.get('tool_life_data', {})
            available_required_tools = [t for t in analysis['tool_numbers']
                                     if t in machine['matching_tools'] and t in tool_life_data]
            
            if available_required_tools:
                output.append("📊 Tool Life Status for Required Tools:")
                for tool in available_required_tools:
                    life_info = tool_life_data[tool]
                    current = life_info.get('current_time', 0)
                    max_time = life_info.get('max_time')
                    percentage = life_info.get('usage_percentage')
                    
                    if max_time is not None and percentage is not None:
                        # Color coding based on usage percentage
                        if percentage >= 90:
                            status = "🔴 Critical"
                        elif percentage >= 75:
                            status = "🟡 High"
                        elif percentage >= 50:
                            status = "🟢 Medium"
                        else:
                            status = "🟢 Low"
                        output.append(f"  T{tool}: {current:.1f}/{max_time:.1f} min ({percentage:.1f}% used) {status}")
                    else:
                        output.append(f"  T{tool}: {current:.1f} min used")
            
            output.append("-" * 40)
        
        # F-value errors
        if analysis['f_value_errors']:
            output.append("\nF-VALUE ERRORS (>80000):")
            for error in analysis['f_value_errors']:
                output.append(f"Line {error['line']}: F{error['value']} - {error['text']}")
        
        self.results_text.insert(tk.END, "\n".join(output))
    
    def calculate_cycle_time(self):
        """Calculate cycle time for the current NC file"""
        nc_file = self.file_path_var.get()
        if not nc_file or not os.path.exists(nc_file):
            messagebox.showerror("Error", "Please select a valid NC file first")
            return
        
        self.status_var.set("Calculating cycle time...")
        self.progress.start()
        
        def calculate_thread():
            try:
                calculator = NCCycleTimeCalculator()
                cycle_data = calculator.parse_nc_file(nc_file)
                
                # Also get basic NC file analysis for additional info
                analysis = self.perform_nc_analysis(nc_file)
                
                # Combine data
                combined_data = {
                    'cycle_data': cycle_data,
                    'analysis': analysis
                }
                
                self.root.after(0, lambda: self.show_cycle_time_results(combined_data))
                
            except Exception as e:
                self.root.after(0, lambda: self.cycle_time_error(str(e)))
        
        threading.Thread(target=calculate_thread, daemon=True).start()
    
    def cycle_time_error(self, error_msg):
        """Called when cycle time calculation fails"""
        self.progress.stop()
        self.status_var.set("Cycle time calculation failed")
        messagebox.showerror("Calculation Error", f"Failed to calculate cycle time:\n{error_msg}")
    
    def show_cycle_time_results(self, data):
        """Show cycle time results in a popup window"""
        self.progress.stop()
        cycle_data = data['cycle_data']
        analysis = data['analysis']
        
        self.status_var.set(f"Cycle time calculated: {cycle_data['total_time_formatted']}")
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title("Cycle Time Analysis Results")
        popup.geometry("800x600")
        popup.resizable(True, True)
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable text widget
        text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=('Courier', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Build results text
        results = []
        results.append("=" * 70)
        results.append("NC FILE CYCLE TIME ANALYSIS")
        results.append("=" * 70)
        results.append(f"File: {analysis['file_name']}")
        results.append(f"Total Cycle Time: {cycle_data['total_time_formatted']}")
        results.append(f"Total Cycle Time (seconds): {cycle_data['total_time']:.2f}")
        results.append("")
        
        # Operation breakdown
        results.append("TIME BREAKDOWN BY OPERATION:")
        results.append("-" * 40)
        for op_type, time_seconds in cycle_data['operation_times'].items():
            if time_seconds > 0:
                count = cycle_data['operation_counts'][op_type]
                formatted_time = self.format_time_simple(time_seconds)
                percentage = (time_seconds / cycle_data['total_time']) * 100 if cycle_data['total_time'] > 0 else 0
                results.append(f"{op_type.title():12}: {formatted_time:>12} ({percentage:5.1f}%) - {count} operations")
        results.append("")
        
        # Tool information
        results.append("TOOL INFORMATION:")
        results.append("-" * 40)
        results.append(f"Total Tools Used: {analysis['total_tools']}")
        results.append(f"Tools: T{', T'.join(analysis['tool_numbers'])}")
        results.append("")
        
        # Stock dimensions
        if analysis['dimensions']:
            dim = analysis['dimensions']
            results.append("STOCK DIMENSIONS:")
            results.append(f"Width:  {dim['width']:.2f} mm")
            results.append(f"Height: {dim['height']:.2f} mm")
            results.append(f"Depth:  {dim['depth']:.2f} mm")
            results.append("")
        
        # Movement analysis
        rapid_moves = [m for m in cycle_data['movements'] if m['type'] == 'rapid']
        feed_moves = [m for m in cycle_data['movements'] if m['type'] == 'feed']
        
        if rapid_moves or feed_moves:
            results.append("MOVEMENT ANALYSIS:")
            results.append("-" * 40)
            
            if rapid_moves:
                total_rapid_distance = sum(m['distance'] for m in rapid_moves)
                avg_rapid_feedrate = sum(m['feedrate'] for m in rapid_moves) / len(rapid_moves)
                results.append(f"Rapid Movements: {len(rapid_moves)} moves")
                results.append(f"Total Rapid Distance: {total_rapid_distance:.2f} mm")
                results.append(f"Average Rapid Rate: {avg_rapid_feedrate:.0f} mm/min")
                results.append("")
            
            if feed_moves:
                total_feed_distance = sum(m['distance'] for m in feed_moves)
                avg_feedrate = sum(m['feedrate'] for m in feed_moves) / len(feed_moves)
                results.append(f"Feed Movements: {len(feed_moves)} moves")
                results.append(f"Total Feed Distance: {total_feed_distance:.2f} mm")
                results.append(f"Average Feed Rate: {avg_feedrate:.0f} mm/min")
                results.append("")
        
        # Cutter compensation info
        comp_on_tools = [tool for tool, info in analysis['cutter_comp_info'].items() if 'On' in info]
        if comp_on_tools:
            results.append("CUTTER COMPENSATION:")
            results.append(f"Tools with compensation: T{', T'.join(comp_on_tools)}")
            results.append("")
        
        # F-value errors
        if analysis['f_value_errors']:
            results.append("F-VALUE WARNINGS (>80000):")
            results.append("-" * 40)
            for error in analysis['f_value_errors'][:5]:  # Show first 5
                results.append(f"Line {error['line']}: F{error['value']}")
            if len(analysis['f_value_errors']) > 5:
                results.append(f"... and {len(analysis['f_value_errors']) - 5} more warnings")
            results.append("")
        
        # Summary
        results.append("SUMMARY:")
        results.append("-" * 40)
        results.append(f"• Total operations: {sum(cycle_data['operation_counts'].values())}")
        results.append(f"• Tool changes: {cycle_data['operation_counts']['tool_change']}")
        results.append(f"• Feed movements: {cycle_data['operation_counts']['feed']}")
        results.append(f"• Rapid movements: {cycle_data['operation_counts']['rapid']}")
        if cycle_data['operation_counts']['dwell'] > 0:
            results.append(f"• Dwell operations: {cycle_data['operation_counts']['dwell']}")
        
        # Insert results into text widget
        text_widget.insert(tk.END, "\n".join(results))
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Add close button
        button_frame = ttk.Frame(popup)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", command=popup.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Save Report",
                  command=lambda: self.save_cycle_time_report(results)).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Calculate position to center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
    
    def format_time_simple(self, seconds):
        """Format time in a simple format for the report"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}min"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def save_cycle_time_report(self, results):
        """Save cycle time report to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Cycle Time Report",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("\n".join(results))
                messagebox.showinfo("Success", f"Report saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save report: {str(e)}")

def main():
    root = tk.Tk()
    app = NCToolAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()