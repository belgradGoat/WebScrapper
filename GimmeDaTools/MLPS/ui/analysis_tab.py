"""
Analysis Tab for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import math
import threading
from typing import Dict, List, Any

from models.analysis_result import AnalysisResult, MachineCompatibility
from utils.event_system import event_system


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


class AnalysisTab:
    """
    Analysis tab for the NC Tool Analyzer application
    """
    def __init__(self, parent, analysis_service, machine_service):
        """
        Initialize the analysis tab
        
        Args:
            parent: Parent widget
            analysis_service: AnalysisService instance
            machine_service: MachineService instance
        """
        self.parent = parent
        self.analysis_service = analysis_service
        self.machine_service = machine_service
        
        # Create frame
        self.frame = ttk.Frame(parent)
        
        # Setup UI components
        self.setup_ui()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Instructions
        instructions = ttk.LabelFrame(self.frame, text="Quick Start", padding=10)
        instructions.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(instructions, text="1. Add machines in 'Machine Management' tab", font=('Arial', 10)).pack(anchor=tk.W)
        ttk.Label(instructions, text="2. Click 'Refresh All Machines' to download current tool data", font=('Arial', 10)).pack(anchor=tk.W)
        ttk.Label(instructions, text="3. Upload NC file below to see tool availability across all machines", font=('Arial', 10)).pack(anchor=tk.W)
        
        # File upload section
        file_frame = ttk.LabelFrame(self.frame, text="NC File Analysis", padding=10)
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
        self.summary_frame = ttk.LabelFrame(self.frame, text="Machine Compatibility Summary", padding=10)
        self.summary_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollable frame for machine cards
        summary_canvas = tk.Canvas(self.summary_frame)
        summary_scrollbar = ttk.Scrollbar(self.summary_frame, orient="vertical", command=summary_canvas.yview)
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
        self._show_initial_message()
        
    def _show_initial_message(self):
        """Show initial message in the summary frame"""
        # Clear existing widgets
        for widget in self.summary_scrollable_frame.winfo_children():
            widget.destroy()
            
        initial_msg = ttk.Label(self.summary_scrollable_frame,
                               text="Upload an NC file and click 'Analyze NC File' to see machine compatibility cards here.\n\n" +
                                    "Each machine will show:\n" +
                                    "• Tool availability status and count\n" +
                                    "• Send to Machine button for direct file transfer\n" +
                                    "• Tool life warnings for critical tools\n" +
                                    "• Missing/locked tool information",
                               font=('Arial', 10), justify=tk.LEFT)
        initial_msg.pack(padx=20, pady=20)
        
    def _setup_event_handlers(self):
        """Set up event handlers for tab events"""
        # Update UI when analysis is complete
        event_system.subscribe("analysis_complete", self.display_summary)
        
        # Update UI when machines are updated
        event_system.subscribe("machines_loaded", lambda _: self.update_status("Machines loaded"))
        event_system.subscribe("machine_updated", lambda _: self.update_status("Machine updated"))
        
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
            
    def refresh_all_machines(self):
        """Download tool data from all machines"""
        machines = self.machine_service.get_all_machines()
        if not machines:
            messagebox.showwarning("Warning", "No machines configured. Add machines first.")
            return
        
        self.update_status("Downloading tool data from all machines...")
        self.progress.start()
        
        # Use a separate thread to avoid blocking the UI
        self._start_background_task(self._refresh_all_machines_task)
        
    def _refresh_all_machines_task(self):
        """Background task for refreshing all machines"""
        machines = self.machine_service.get_all_machines()
        success_count = 0
        total_count = len(machines)
        results = []
        
        for machine_id in machines:
            self.update_status(f"Downloading from {machine_id}...")
            success, message = self.machine_service.download_from_machine(machine_id)
            
            if success:
                success_count += 1
                results.append(f"✅ {machine_id}: {message}")
            else:
                results.append(f"❌ {machine_id}: {message}")
        
        # Update UI in main thread
        self.frame.after(0, lambda: self._refresh_complete(success_count, total_count, results))
        
    def _refresh_complete(self, success_count, total_count, results):
        """Called when refresh is complete"""
        self.progress.stop()
        
        # Show results
        result_text = f"Download Complete: {success_count}/{total_count} machines updated\n\n"
        result_text += "\n".join(results)
        
        self.update_status(f"Complete: {success_count}/{total_count} machines updated")
        messagebox.showinfo("Download Complete", result_text)
        
    def analyze_nc_file(self):
        """Analyze the uploaded NC file"""
        nc_file = self.file_path_var.get()
        if not nc_file or not os.path.exists(nc_file):
            messagebox.showerror("Error", "Please select a valid NC file")
            return
        
        machines = self.machine_service.get_all_machines()
        if not machines:
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
        
        # Use a separate thread to avoid blocking the UI
        self._start_background_task(lambda: self._analyze_nc_file_task(nc_file, refresh_tools))
        
    def _analyze_nc_file_task(self, nc_file, refresh_tools):
        """Background task for analyzing NC file"""
        try:
            self.update_status("Analyzing NC file...")
            analysis_result = self.analysis_service.analyze_nc_file(nc_file, refresh_tools)
            
            # Update UI in main thread
            self.frame.after(0, lambda: self._analysis_complete(analysis_result))
            
        except Exception as e:
            # Update UI in main thread
            self.frame.after(0, lambda: self._analysis_error(str(e)))
            
    def _analysis_complete(self, analysis_result):
        """Called when analysis is complete"""
        self.progress.stop()
        self.update_status(f"Analysis complete: {analysis_result.total_tools} tools required")
        
        # Display summary is handled by the event handler
        
    def _analysis_error(self, error_msg):
        """Called when analysis fails"""
        self.progress.stop()
        self.update_status("Analysis failed")
        messagebox.showerror("Analysis Error", f"Failed to analyze NC file:\n{error_msg}")
        
    def display_summary(self, analysis_result: AnalysisResult):
        """
        Display machine cards in Analysis tab
        
        Args:
            analysis_result: AnalysisResult object
        """
        # Clear existing widgets
        for widget in self.summary_scrollable_frame.winfo_children():
            widget.destroy()
        
        # File info header
        header_frame = ttk.Frame(self.summary_scrollable_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text=f"📄 File: {analysis_result.file_name}", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text=f"🔧 Tools Required: {analysis_result.total_tools}", font=('Arial', 10)).pack(anchor=tk.W)
        
        if analysis_result.download_info:
            ttk.Label(header_frame, text=f"📊 {analysis_result.download_info}", font=('Arial', 10)).pack(anchor=tk.W)
        
        ttk.Separator(self.summary_scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=10)
        
        # Create machine cards (ranked by compatibility)
        for i, machine in enumerate(analysis_result.machine_analysis, 1):
            self._create_machine_card(machine, analysis_result, i)
        
        # Footer note
        footer_frame = ttk.Frame(self.summary_scrollable_frame)
        footer_frame.pack(fill=tk.X, padx=10, pady=20)
        
        footer_text = ttk.Label(footer_frame,
                               text="💡 Switch to 'Results' tab for detailed analysis including tool sequences, dimensions, and debug info",
                               font=('Arial', 9), foreground='blue')
        footer_text.pack(anchor=tk.W)
        
    def _create_machine_card(self, machine: MachineCompatibility, analysis_result: AnalysisResult, rank: int):
        """
        Create individual machine card
        
        Args:
            machine: MachineCompatibility object
            analysis_result: AnalysisResult object
            rank: Rank of the machine in the compatibility list
        """
        available_tools = len(machine.matching_tools)
        total_required = analysis_result.total_tools
        missing_count = len(machine.missing_tools)
        locked_count = len(machine.locked_required_tools)
        
        # Determine card color based on match level
        if machine.match_percentage == 100:
            card_color = '#d4edda'  # Green
            border_color = '#28a745'
        elif machine.match_percentage >= 80:
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
        
        match_text = f"{machine.match_percentage}% Match" if machine.match_percentage > 0 else "No Tools Available"
        match_label = tk.Label(header_frame, text=match_text, font=('Arial', 14, 'bold'), bg=card_color)
        match_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Machine info
        info_frame = tk.Frame(content_frame, bg=card_color)
        info_frame.pack(fill=tk.X, pady=5)
        
        machine_name = tk.Label(info_frame, text=f"🏭 {machine.machine_name} ({machine.machine_id})",
                               font=('Arial', 12, 'bold'), bg=card_color)
        machine_name.pack(anchor=tk.W)
        
        location_label = tk.Label(info_frame, text=f"📍 {machine.location}", font=('Arial', 10), bg=card_color)
        location_label.pack(anchor=tk.W)
        
        tools_label = tk.Label(info_frame, text=f"🔧 Tools: {available_tools}/{total_required} available",
                              font=('Arial', 10), bg=card_color)
        tools_label.pack(anchor=tk.W)
        
        # Status and issues
        status_frame = tk.Frame(content_frame, bg=card_color)
        status_frame.pack(fill=tk.X, pady=5)
        
        # Show missing tools if any
        if missing_count > 0:
            missing_tools = machine.missing_tools[:3]
            missing_text = f"❌ Missing: T{', T'.join(missing_tools)}"
            if len(machine.missing_tools) > 3:
                missing_text += f" (+{len(machine.missing_tools) - 3} more)"
            missing_label = tk.Label(status_frame, text=missing_text, font=('Arial', 9), bg=card_color, fg='red')
            missing_label.pack(anchor=tk.W)
        
        # Show locked tools if any
        if locked_count > 0:
            locked_tools = machine.locked_required_tools[:3]
            locked_text = f"🔒 Locked: T{', T'.join(locked_tools)}"
            if len(machine.locked_required_tools) > 3:
                locked_text += f" (+{len(machine.locked_required_tools) - 3} more)"
            locked_label = tk.Label(status_frame, text=locked_text, font=('Arial', 9), bg=card_color, fg='orange')
            locked_label.pack(anchor=tk.W)
        
        # Tool life warnings
        machine_obj = self.machine_service.get_machine(machine.machine_id)
        if machine_obj:
            tool_life_data = machine_obj.tool_life_data
            critical_tools = []
            
            for tool in machine.matching_tools:
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
                             command=lambda m=machine: self._send_to_machine(m))
        send_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # View Details button
        details_btn = ttk.Button(button_frame, text="📋 View Details",
                                command=lambda: self.parent.select(2))  # Switch to Results tab
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
            
    def _send_to_machine(self, machine: MachineCompatibility):
        """
        Send NC file to machine
        
        Args:
            machine: MachineCompatibility object
        """
        if not self.analysis_service.current_analysis:
            messagebox.showerror("Error", "No NC file analysis available")
            return
        
        # Get the original NC file path
        nc_file_path = self.file_path_var.get()
        if not nc_file_path or not os.path.exists(nc_file_path):
            messagebox.showerror("Error", "Original NC file not found. Please select the NC file again.")
            return
        
        # Confirm the transfer
        result = messagebox.askyesno(
            "Send File to Machine",
            f"Send '{self.analysis_service.current_analysis.file_name}' to {machine.machine_name}?\n\n" +
            f"Machine: {machine.machine_name} ({machine.machine_id})\n" +
            f"Match: {machine.match_percentage}% ({len(machine.matching_tools)}/{self.analysis_service.current_analysis.total_tools} tools)\n\n" +
            "The file will be uploaded to the machine's TNC folder."
        )
        
        if not result:
            return
        
        # Show progress
        self.update_status(f"Sending {self.analysis_service.current_analysis.file_name} to {machine.machine_name}...")
        self.progress.start()
        
        # Use a separate thread to avoid blocking the UI
        self._start_background_task(lambda: self._send_file_task(machine.machine_id, nc_file_path))
        
    def _send_file_task(self, machine_id, file_path):
        """Background task for sending file to machine"""
        try:
            success, message = self.machine_service.send_file_to_machine(machine_id, file_path)
            
            # Update UI in main thread
            self.frame.after(0, lambda: self._send_complete(success, machine_id, message))
            
        except Exception as e:
            # Update UI in main thread
            self.frame.after(0, lambda: self._send_complete(False, machine_id, str(e)))
            
    def _send_complete(self, success, machine_id, message):
        """Called when file send is complete"""
        self.progress.stop()
        
        machine = self.machine_service.get_machine(machine_id)
        machine_name = machine.name if machine else machine_id
        
        if success:
            self.update_status(f"✅ File sent to {machine_name}")
            messagebox.showinfo("Success", message)
        else:
            self.update_status(f"❌ Failed to send to {machine_name}")
            messagebox.showerror("Send Failed", message)
            
    def update_status(self, message):
        """Update the status message"""
        self.status_var.set(message)
        self.frame.update_idletasks()
        
    def calculate_cycle_time(self):
        """Calculate cycle time for the current NC file"""
        nc_file = self.file_path_var.get()
        if not nc_file or not os.path.exists(nc_file):
            messagebox.showerror("Error", "Please select a valid NC file first")
            return
        
        self.update_status("Calculating cycle time...")
        self.progress.start()
        
        # Use a separate thread to avoid blocking the UI
        self._start_background_task(lambda: self._calculate_cycle_time_task(nc_file))
    
    def _calculate_cycle_time_task(self, nc_file):
        """Background task for calculating cycle time"""
        try:
            calculator = NCCycleTimeCalculator()
            cycle_data = calculator.parse_nc_file(nc_file)
            
            # Also get basic NC file analysis for additional info
            analysis_result = self.analysis_service.analyze_nc_file(nc_file, refresh_tools=False)
            
            # Combine data
            combined_data = {
                'cycle_data': cycle_data,
                'analysis': analysis_result
            }
            
            # Update UI in main thread
            self.frame.after(0, lambda: self._cycle_time_complete(combined_data))
            
        except Exception as e:
            # Update UI in main thread
            self.frame.after(0, lambda: self._cycle_time_error(str(e)))
    
    def _cycle_time_complete(self, data):
        """Called when cycle time calculation is complete"""
        self.progress.stop()
        cycle_data = data['cycle_data']
        analysis = data['analysis']
        
        self.update_status(f"Cycle time calculated: {cycle_data['total_time_formatted']}")
        
        # Show results in popup
        self.show_cycle_time_results(data)
    
    def _cycle_time_error(self, error_msg):
        """Called when cycle time calculation fails"""
        self.progress.stop()
        self.update_status("Cycle time calculation failed")
        messagebox.showerror("Calculation Error", f"Failed to calculate cycle time:\n{error_msg}")
    
    def show_cycle_time_results(self, data):
        """Show cycle time results in a popup window"""
        cycle_data = data['cycle_data']
        analysis = data['analysis']
        
        # Create popup window
        popup = tk.Toplevel(self.frame)
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
        results.append(f"File: {analysis.file_name}")
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
        results.append(f"Total Tools Used: {analysis.total_tools}")
        results.append(f"Tools: T{', T'.join(analysis.tool_numbers)}")
        results.append("")
        
        # Stock dimensions
        if analysis.dimensions:
            dim = analysis.dimensions
            results.append("STOCK DIMENSIONS:")
            results.append(f"Width:  {dim.width:.2f} mm")
            results.append(f"Height: {dim.height:.2f} mm")
            results.append(f"Depth:  {dim.depth:.2f} mm")
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
        comp_on_tools = [tool for tool, info in analysis.cutter_comp_info.items() if 'On' in info]
        if comp_on_tools:
            results.append("CUTTER COMPENSATION:")
            results.append(f"Tools with compensation: T{', T'.join(comp_on_tools)}")
            results.append("")
        
        # F-value errors
        if analysis.f_value_errors:
            results.append("F-VALUE WARNINGS (>80000):")
            results.append("-" * 40)
            for error in analysis.f_value_errors[:5]:  # Show first 5
                results.append(f"Line {error['line']}: F{error['value']}")
            if len(analysis.f_value_errors) > 5:
                results.append(f"... and {len(analysis.f_value_errors) - 5} more warnings")
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
        popup.transient(self.frame)
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

    def _start_background_task(self, task_func):
        """
        Start a background task in a separate thread
        
        Args:
            task_func: Function to run in the background
        """
        thread = threading.Thread(target=task_func, daemon=True)
        thread.start()