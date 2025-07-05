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
from datetime import datetime

from models.analysis_result import AnalysisResult, MachineCompatibility
from models.job import Job
from models.part import Part
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
    def __init__(self, parent, analysis_service, machine_service, scheduler_service=None, jms_service=None):
        """
        Initialize the analysis tab
        
        Args:
            parent: Parent widget
            analysis_service: AnalysisService instance
            machine_service: MachineService instance
            scheduler_service: SchedulerService instance (optional)
            jms_service: JMSService instance (optional)
        """
        self.parent = parent
        self.analysis_service = analysis_service
        self.machine_service = machine_service
        self.scheduler_service = scheduler_service
        self.jms_service = jms_service
        
        # Create frame
        self.frame = ttk.Frame(parent)
        
        # Track last calculated cycle time for job creation
        self.last_cycle_time = None
        self.last_analysis_data = None
        
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
        ttk.Button(button_frame, text="🔍 Check Machine Compatibility", command=self.analyze_nc_file).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(button_frame, text="⏱️ Calculate Cycle Time", command=self.calculate_cycle_time).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(button_frame, text="📊 Calculate Material Removal Rates", command=self.calculate_material_removal_rates).pack(side=tk.LEFT, padx=(0,10))
        ttk.Button(button_frame, text="�️ Create Job from File", command=self.create_job_from_file).pack(side=tk.LEFT)
        
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
        
        # Store the data for job creation
        self.last_cycle_time = cycle_data['total_time'] / 60.0  # Convert to minutes
        self.last_analysis_data = data
        
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

    def calculate_material_removal_rates(self):
        """Calculate material removal rates for the current NC file"""
        nc_file = self.file_path_var.get()
        if not nc_file or not os.path.exists(nc_file):
            messagebox.showerror("Error", "Please select a valid NC file first")
            return
        
        self.update_status("Calculating material removal rates...")
        self.progress.start()
        
        # Use a separate thread to avoid blocking the UI
        self._start_background_task(lambda: self._calculate_mrr_task(nc_file))
    
    def _calculate_mrr_task(self, nc_file):
        """Background task for calculating material removal rates"""
        try:
            from services.material_removal_calculator import MaterialRemovalCalculator
            
            calculator = MaterialRemovalCalculator()
            
            # Calculate MRR for each tool
            mrr_results = calculator.analyze_nc_file_mrr(nc_file)
            
            # Combine with file info
            combined_data = {
                'mrr_results': mrr_results,
                'file_name': os.path.basename(nc_file)
            }
            
            # Update UI in main thread
            self.frame.after(0, lambda: self._mrr_complete(combined_data))
            
        except Exception as e:
            # Update UI in main thread
            self.frame.after(0, lambda: self._mrr_error(str(e)))

    def _mrr_complete(self, data):
        """Called when MRR calculation is complete"""
        self.progress.stop()
        self.update_status("Material removal rates calculated")
        
        # Show results in popup
        self.show_mrr_results(data)

    def _mrr_error(self, error_msg):
        """Called when MRR calculation fails"""
        self.progress.stop()
        self.update_status("MRR calculation failed")
        messagebox.showerror("Calculation Error", f"Failed to calculate material removal rates:\n{error_msg}")

    def show_mrr_results(self, data):
        """Show material removal rate results in a popup window"""
        mrr_results = data['mrr_results']
        file_name = data['file_name']
        
        if not mrr_results:
            messagebox.showinfo("No Results", "No tools with material removal data found in the NC file.")
            return
        
        # Create popup window
        popup = tk.Toplevel(self.frame)
        popup.title("Material Removal Rate Analysis Results")
        popup.geometry("900x700")
        popup.resizable(True, True)
        
        # Main frame with scrollbar
        main_frame = ttk.Frame(popup)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable text widget
        text_widget = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, font=('Courier', 10))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Build results text
        results = []
        results.append("=" * 80)
        results.append("MATERIAL REMOVAL RATE ANALYSIS")
        results.append("=" * 80)
        results.append(f"File: {file_name}")
        results.append(f"Tools Analyzed: {len(mrr_results)}")
        results.append("")
        
        # Calculate summary statistics
        total_material_removed_mm3 = sum(result.total_material_removed_mm3 for result in mrr_results.values())
        total_material_removed_m3 = sum(result.total_material_removed_m3 for result in mrr_results.values())
        tools_with_data = [r for r in mrr_results.values() if r.total_material_removed_mm3 > 0]
        
        if tools_with_data:
            avg_mrr_mm3 = sum(r.average_mrr_mm3_per_min for r in tools_with_data) / len(tools_with_data)
            avg_mrr_m3 = sum(r.average_mrr_m3_per_min for r in tools_with_data) / len(tools_with_data)
            max_mrr_tool = max(tools_with_data, key=lambda x: x.average_mrr_mm3_per_min)
            min_mrr_tool = min(tools_with_data, key=lambda x: x.average_mrr_mm3_per_min)
        else:
            avg_mrr_mm3 = 0
            avg_mrr_m3 = 0
            max_mrr_tool = None
            min_mrr_tool = None
        
        # Tool analysis results
        results.append("TOOL ANALYSIS RESULTS:")
        results.append("-" * 80)
        
        for tool_num, result in sorted(mrr_results.items()):
            results.append("")
            results.append(f"Tool T{result.tool_number}")
            
            # Tool information
            if result.tool_info:
                tool_info = result.tool_info
                results.append(f"  Type: {tool_info.tool_type_name or 'Unknown'} ({tool_info.tool_type or 'N/A'})")
                if tool_info.diameter:
                    results.append(f"  Diameter: {tool_info.diameter:.2f} mm")
                if tool_info.tool_holder:
                    results.append(f"  Tool Holder: {tool_info.tool_holder}")
                if tool_info.flute_length:
                    results.append(f"  Flute Length: {tool_info.flute_length:.1f} mm")
                if tool_info.corner_radius:
                    results.append(f"  Corner Radius: {tool_info.corner_radius:.2f} mm")
                if tool_info.material_code:
                    results.append(f"  Material: {tool_info.material_code}")
                if tool_info.flute_count:
                    results.append(f"  Flutes: {tool_info.flute_count}")
            else:
                results.append("  Type: Information not found in comments")
            
            results.append("")
            results.append("  Machining Operations:")
            
            if result.total_cutting_distance > 0:
                results.append(f"  • Total Cutting Distance: {result.total_cutting_distance:.1f} mm")
                results.append(f"  • Average Feed Rate: {result.average_feed_rate:.0f} mm/min")
                results.append(f"  • Average Depth of Cut: {result.average_doc:.2f} mm")
                results.append(f"  • Average Width of Cut: {result.average_woc:.2f} mm")
                results.append(f"  • Material Removal Rate: {result.average_mrr_mm3_per_min:.0f} mm³/min")
                results.append(f"  • Material Removal Rate: {result.average_mrr_m3_per_min:.6f} m³/min")
                results.append(f"  • Cutting Time: {result.total_cutting_time:.1f} minutes")
                results.append(f"  • Material Removed: {result.total_material_removed_mm3:.0f} mm³")
                results.append(f"  • Material Removed: {result.total_material_removed_m3:.9f} m³")
                results.append(f"  • Number of Operations: {len(result.cutting_moves)}")
                
                # Show machining strategies
                if result.machining_strategies:
                    strategy_list = [f"{strategy}({count})" for strategy, count in result.machining_strategies.items()]
                    results.append(f"  • Machining Strategies: {', '.join(strategy_list)}")
                
                # Show warnings if any
                if result.warnings:
                    results.append("  • Warnings:")
                    for warning in result.warnings:
                        results.append(f"    - {warning}")
            else:
                results.append("  • No cutting operations detected")
        
        # Summary section
        results.append("")
        results.append("SUMMARY:")
        results.append("-" * 80)
        results.append(f"• Total Material Removed: {total_material_removed_mm3:.0f} mm³")
        results.append(f"• Total Material Removed: {total_material_removed_m3:.9f} m³")
        
        if tools_with_data:
            results.append(f"• Average MRR across all tools: {avg_mrr_mm3:.0f} mm³/min")
            results.append(f"• Average MRR across all tools: {avg_mrr_m3:.6f} m³/min")
            results.append(f"• Most Efficient Tool: T{max_mrr_tool.tool_number} ({max_mrr_tool.average_mrr_mm3_per_min:.0f} mm³/min)")
            results.append(f"• Least Efficient Tool: T{min_mrr_tool.tool_number} ({min_mrr_tool.average_mrr_mm3_per_min:.0f} mm³/min)")
            
            # Categorize tools
            high_mrr_tools = [r for r in tools_with_data if r.average_mrr_mm3_per_min > 5000]
            low_mrr_tools = [r for r in tools_with_data if r.average_mrr_mm3_per_min < 1000]
            
            if high_mrr_tools:
                tool_list = ", ".join([f"T{t.tool_number}" for t in high_mrr_tools])
                results.append(f"• High MRR Tools (>5000 mm³/min): {tool_list}")
            
            if low_mrr_tools:
                tool_list = ", ".join([f"T{t.tool_number}" for t in low_mrr_tools])
                results.append(f"• Low MRR Tools (<1000 mm³/min): {tool_list}")
        else:
            results.append("• No tools with cutting operations found")
        
        # Tool information summary
        tools_with_info = sum(1 for r in mrr_results.values() if r.tool_info)
        tools_with_diameter = sum(1 for r in mrr_results.values() if r.tool_info and r.tool_info.diameter)
        
        results.append("")
        results.append("TOOL INFORMATION COVERAGE:")
        results.append("-" * 40)
        results.append(f"• Tools with comment information: {tools_with_info}/{len(mrr_results)}")
        results.append(f"• Tools with diameter data: {tools_with_diameter}/{len(mrr_results)}")
        
        if tools_with_diameter < len(mrr_results):
            results.append("• Consider adding tool comments for more accurate calculations")
        
        # Insert results into text widget
        text_widget.insert(tk.END, "\n".join(results))
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Add buttons
        button_frame = ttk.Frame(popup)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", command=popup.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Save Report",
                  command=lambda: self.save_mrr_report(results)).pack(side=tk.RIGHT, padx=(0, 10))
        
        # Center the popup
        popup.transient(self.frame)
        popup.grab_set()
        
        # Calculate position to center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")

    def save_mrr_report(self, results):
        """Save material removal rate report to file"""
        filename = filedialog.asksaveasfilename(
            title="Save Material Removal Rate Report",
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

    def create_job_from_file(self):
        """Create a job from the current NC file"""
        nc_file = self.file_path_var.get()
        if not nc_file or not os.path.exists(nc_file):
            messagebox.showerror("Error", "Please select a valid NC file first")
            return
        
        if not self.scheduler_service:
            messagebox.showerror("Error", "Scheduler service not available")
            return
        
        # Show job creation dialog
        self._show_job_creation_dialog(nc_file)
    
    def _show_job_creation_dialog(self, nc_file):
        """Show the job creation dialog"""
        dialog = JobCreationDialog(
            self.frame,
            nc_file,
            self.scheduler_service,
            self.machine_service,
            self.last_cycle_time,
            self.last_analysis_data,
            self.jms_service
        )
        
    def _start_background_task(self, task_func):
        """
        Start a background task in a separate thread
        
        Args:
            task_func: Function to run in the background
        """
        thread = threading.Thread(target=task_func, daemon=True)
        thread.start()


class JobCreationDialog:
    """Dialog for creating a job from an NC file"""
    
    def __init__(self, parent, nc_file_path, scheduler_service, machine_service,
                 cycle_time=None, analysis_data=None, jms_service=None):
        """
        Initialize the job creation dialog
        
        Args:
            parent: Parent widget
            nc_file_path: Path to the NC file
            scheduler_service: SchedulerService instance
            machine_service: MachineService instance
            cycle_time: Calculated cycle time in minutes (optional)
            analysis_data: Analysis data from cycle time calculation (optional)
            jms_service: JMSService instance (optional)
        """
        self.parent = parent
        self.nc_file_path = nc_file_path
        self.scheduler_service = scheduler_service
        self.machine_service = machine_service
        self.jms_service = jms_service
        self.cycle_time = cycle_time or 10.0  # Default to 10 minutes
        self.analysis_data = analysis_data
        
        # Extract filename
        self.filename = os.path.basename(nc_file_path)
        self.job_name = os.path.splitext(self.filename)[0]  # Remove extension
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Job from File")
        self.dialog.geometry("700x650")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Form variables
        self.job_name_var = tk.StringVar(value=self.job_name)
        self.machine_id_var = tk.StringVar()
        self.total_parts_var = tk.IntVar(value=1)
        self.cycle_time_var = tk.DoubleVar(value=self.cycle_time)
        self.start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.start_hour_var = tk.IntVar(value=8)
        self.start_minute_var = tk.IntVar(value=0)
        
        # Store widget references for disabling/enabling
        self.machine_combo = None
        self.start_date_entry = None
        self.start_hour_spinbox = None
        self.start_minute_spinbox = None
        
        # JMS integration flag - default to True if JMS service is available
        self.create_jms_order_var = tk.BooleanVar(value=bool(self.jms_service))
        
        # Scheduling options (mutually exclusive)
        self.find_next_slot_var = tk.BooleanVar(value=False)
        self.optimize_schedule_var = tk.BooleanVar(value=False)
        
        # Setup UI
        self._setup_ui()
        
        # Center the dialog
        self._center_dialog()
        
    def _setup_ui(self):
        """Setup the dialog UI"""
        # Main frame
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="Create Job from NC File",
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # File info section
        file_frame = ttk.LabelFrame(main_frame, text="File Information", padding=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text=f"File: {self.filename}", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(file_frame, text=f"Path: {self.nc_file_path}", font=('Arial', 9)).pack(anchor=tk.W)
        
        # Show cycle time if available
        if self.analysis_data:
            cycle_data = self.analysis_data['cycle_data']
            analysis = self.analysis_data['analysis']
            
            ttk.Label(file_frame, text=f"Calculated Cycle Time: {cycle_data['total_time_formatted']}",
                     font=('Arial', 9), foreground='blue').pack(anchor=tk.W)
            ttk.Label(file_frame, text=f"Tools Required: {analysis.total_tools}",
                     font=('Arial', 9)).pack(anchor=tk.W)
        
        # Job details section
        job_frame = ttk.LabelFrame(main_frame, text="Job Details", padding=10)
        job_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create grid
        job_grid = ttk.Frame(job_frame)
        job_grid.pack(fill=tk.X)
        
        # Job name
        ttk.Label(job_grid, text="Job Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(job_grid, textvariable=self.job_name_var, width=30).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Machine selection
        ttk.Label(job_grid, text="Initial Machine:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.machine_combo = ttk.Combobox(job_grid, textvariable=self.machine_id_var, width=20)
        self.machine_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Populate machine options
        machines = self.machine_service.get_all_machines()
        if machines:
            self.machine_options = [(m.machine_id, f"{m.name} ({m.machine_id})") for m in machines.values()]
            self.machine_combo['values'] = [m[1] for m in self.machine_options]
            # Set first machine as default
            if self.machine_options:
                self.machine_combo.current(0)
                self.machine_id_var.set(self.machine_options[0][0])
            
            def on_machine_select(event):
                selected_index = self.machine_combo.current()
                if selected_index >= 0:
                    self.machine_id_var.set(self.machine_options[selected_index][0])
            
            self.machine_combo.bind('<<ComboboxSelected>>', on_machine_select)
        
        # Total parts
        ttk.Label(job_grid, text="Number of Parts:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(job_grid, from_=1, to=100, textvariable=self.total_parts_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Cycle time
        ttk.Label(job_grid, text="Cycle Time per Part (min):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        ttk.Spinbox(job_grid, from_=0.1, to=1000, increment=0.1, textvariable=self.cycle_time_var, width=10).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Start date
        ttk.Label(job_grid, text="Start Date:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.start_date_entry = ttk.Entry(job_grid, textvariable=self.start_date_var, width=15)
        self.start_date_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Start time
        ttk.Label(job_grid, text="Start Time:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=2)
        time_frame = ttk.Frame(job_grid)
        time_frame.grid(row=2, column=3, sticky=tk.W, padx=5, pady=2)
        
        self.start_hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.start_hour_var, width=5)
        self.start_hour_spinbox.pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.start_minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.start_minute_var, width=5)
        self.start_minute_spinbox.pack(side=tk.LEFT)
        
        # Total time calculation
        self.total_time_label = ttk.Label(job_grid, text="")
        self.total_time_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=2)
        
        # Update total time when values change
        self.total_parts_var.trace_add('write', self._update_total_time)
        self.cycle_time_var.trace_add('write', self._update_total_time)
        self._update_total_time()
        
        # Scheduling Options section
        schedule_frame = ttk.LabelFrame(main_frame, text="Intelligent Scheduling", padding=10)
        schedule_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(schedule_frame, text="Override manual start time with intelligent scheduling:",
                 font=('Arial', 9)).pack(anchor=tk.W)
        
        # Create scheduling checkboxes (mutually exclusive)
        schedule_options_frame = ttk.Frame(schedule_frame)
        schedule_options_frame.pack(fill=tk.X, pady=(5, 0))
        
        find_slot_cb = ttk.Checkbutton(schedule_options_frame,
                                      text="🔍 Find Next Available Time Slot",
                                      variable=self.find_next_slot_var,
                                      command=self._on_find_slot_toggle)
        find_slot_cb.pack(anchor=tk.W, pady=2)
        
        optimize_cb = ttk.Checkbutton(schedule_options_frame,
                                     text="⚡ Optimize Production Schedule",
                                     variable=self.optimize_schedule_var,
                                     command=self._on_optimize_toggle)
        optimize_cb.pack(anchor=tk.W, pady=2)
        
        # Help text
        ttk.Label(schedule_frame,
                 text="• Find Next Available: Finds machine with earliest available time + required tools\n"
                      "• Optimize Schedule: Uses advanced algorithms to fit job optimally (when available)",
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W, pady=(5, 0))
        
        # JMS Integration section
        jms_available = bool(self.jms_service)
        jms_title = "JMS Integration" if jms_available else "JMS Integration (Not Available)"
        jms_frame = ttk.LabelFrame(main_frame, text=jms_title, padding=10)
        jms_frame.pack(fill=tk.X, pady=(0, 10))
        
        if jms_available:
            ttk.Checkbutton(jms_frame, text="Create JMS Work Order and Lock Job",
                           variable=self.create_jms_order_var).pack(anchor=tk.W)
            ttk.Label(jms_frame, text="Job will be created as 'locked' and transferred to JMS",
                     font=('Arial', 9), foreground='blue').pack(anchor=tk.W)
        else:
            ttk.Checkbutton(jms_frame, text="Create JMS Work Order (Not Available)",
                           variable=self.create_jms_order_var, state=tk.DISABLED).pack(anchor=tk.W)
            ttk.Label(jms_frame, text="JMS service not configured. Job will be created as 'active'",
                     font=('Arial', 9), foreground='gray').pack(anchor=tk.W)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Create Job", command=self._create_job).pack(side=tk.RIGHT)
        
    def _update_total_time(self, *args):
        """Update the total time calculation"""
        try:
            total_parts = self.total_parts_var.get()
            cycle_time = self.cycle_time_var.get()
            total_minutes = total_parts * cycle_time
            total_hours = total_minutes / 60
            
            self.total_time_label.config(
                text=f"Total Time: {total_minutes:.1f} minutes ({total_hours:.1f} hours)"
            )
        except (ValueError, tk.TclError):
            self.total_time_label.config(text="Total Time: Invalid input")
    
    def _on_find_slot_toggle(self):
        """Handle find next slot checkbox toggle (mutually exclusive)"""
        if self.find_next_slot_var.get():
            self.optimize_schedule_var.set(False)
            # Disable manual machine and date selection
            self._set_manual_controls_state(tk.DISABLED)
        else:
            # Re-enable manual controls
            self._set_manual_controls_state(tk.NORMAL)
    
    def _on_optimize_toggle(self):
        """Handle optimize schedule checkbox toggle (mutually exclusive)"""
        if self.optimize_schedule_var.get():
            self.find_next_slot_var.set(False)
            # Disable manual machine and date selection
            self._set_manual_controls_state(tk.DISABLED)
        else:
            # Re-enable manual controls
            self._set_manual_controls_state(tk.NORMAL)
    
    def _set_manual_controls_state(self, state):
        """Enable or disable manual scheduling controls"""
        if self.machine_combo:
            self.machine_combo.configure(state=state)
        if self.start_date_entry:
            self.start_date_entry.configure(state=state)
        if self.start_hour_spinbox:
            self.start_hour_spinbox.configure(state=state)
        if self.start_minute_spinbox:
            self.start_minute_spinbox.configure(state=state)
    
    def _find_next_available_slot(self, job_name, total_parts, cycle_time):
        """
        Find the next available time slot for a job with tool availability checking
        
        Args:
            job_name: Name of the job (for tool analysis if NC data available)
            total_parts: Number of parts
            cycle_time: Cycle time per part in minutes
            
        Returns:
            Tuple of (machine_id, start_timestamp, start_date, start_hour, start_minute)
        """
        machines = self.machine_service.get_all_machines()
        if not machines:
            return None, None, None, None, None
        
        # Get required tools from analysis data if available
        required_tools = []
        if self.analysis_data and 'analysis' in self.analysis_data:
            analysis = self.analysis_data['analysis']
            required_tools = analysis.tool_numbers
        
        # Calculate job duration in milliseconds (preferably whole order, minimum one part)
        single_part_duration_ms = int(cycle_time * 60 * 1000)
        full_order_duration_ms = int(total_parts * cycle_time * 60 * 1000)
        
        # Start search from current time
        search_start = int(datetime.now().timestamp() * 1000)
        
        best_slots = []  # Store all valid slots with scoring
        
        # Check each machine
        for machine_id, machine in machines.items():
            # Check tool availability if we have tool requirements and analysis data
            if required_tools and self.analysis_data and 'analysis' in self.analysis_data:
                analysis_result = self.analysis_data['analysis']
                
                # Find this machine in the analysis results
                machine_compatibility = None
                for machine_analysis in analysis_result.machine_analysis:
                    if machine_analysis.machine_id == machine_id:
                        machine_compatibility = machine_analysis
                        break
                
                # Skip machines that weren't analyzed or have missing tools
                if not machine_compatibility or machine_compatibility.missing_tools:
                    continue  # Skip machines without all required tools
            
            # Get all parts scheduled on this machine
            all_parts = self.scheduler_service.get_all_parts()
            machine_parts = [p for p in all_parts.values() if p.machine_id == machine_id]
            
            # Sort by start time
            machine_parts.sort(key=lambda p: p.start_time)
            
            # Find gaps in the schedule
            current_time = search_start
            
            for part in machine_parts:
                # Check if there's a gap for full order first
                if part.start_time - current_time >= full_order_duration_ms:
                    # Found slot for full order - high priority
                    best_slots.append({
                        'machine_id': machine_id,
                        'start_time': current_time,
                        'duration_fit': 'full_order',
                        'priority': 1
                    })
                    break
                # Check if there's a gap for at least one part
                elif part.start_time - current_time >= single_part_duration_ms:
                    # Found slot for at least one part - lower priority
                    best_slots.append({
                        'machine_id': machine_id,
                        'start_time': current_time,
                        'duration_fit': 'single_part',
                        'priority': 2
                    })
                    break
                
                # Move past this part
                job = self.scheduler_service.get_job(part.job_id)
                if job:
                    part_duration = int(job.cycle_time * 60 * 1000)
                    current_time = max(current_time, part.start_time + part_duration)
            else:
                # No conflicting parts, can fit full order after last part
                best_slots.append({
                    'machine_id': machine_id,
                    'start_time': current_time,
                    'duration_fit': 'full_order',
                    'priority': 1
                })
        
        if best_slots:
            # Sort by priority (full order first), then by earliest time
            best_slots.sort(key=lambda x: (x['priority'], x['start_time']))
            best_slot = best_slots[0]
            
            machine_id = best_slot['machine_id']
            start_timestamp = best_slot['start_time']
            start_datetime = datetime.fromtimestamp(start_timestamp / 1000)
            
            return (
                machine_id,
                start_timestamp,
                start_datetime.strftime("%Y-%m-%d"),
                start_datetime.hour,
                start_datetime.minute
            )
        
        return None, None, None, None, None
    
    def _optimize_production_schedule(self, job_name, total_parts, cycle_time):
        """
        Optimize production schedule placement (placeholder for advanced algorithm)
        
        Args:
            job_name: Name of the job
            total_parts: Number of parts
            cycle_time: Cycle time per part in minutes
            
        Returns:
            Tuple of (machine_id, start_timestamp, start_date, start_hour, start_minute)
        """
        # For now, use the same logic as find_next_available_slot
        # In the future, this could implement more sophisticated algorithms like:
        # - Machine utilization balancing
        # - Tool change minimization
        # - Rush order prioritization
        # - Setup time optimization
        
        return self._find_next_available_slot(job_name, total_parts, cycle_time)
    
    def _center_dialog(self):
        """Center the dialog on the parent window"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def _cancel(self):
        """Cancel job creation"""
        self.dialog.destroy()
    
    def _create_job(self):
        """Create the job"""
        try:
            # Validate inputs
            job_name = self.job_name_var.get().strip()
            if not job_name:
                messagebox.showerror("Error", "Job name is required", parent=self.dialog)
                return
            
            machine_id = self.machine_id_var.get()
            if not machine_id:
                messagebox.showerror("Error", "Machine selection is required", parent=self.dialog)
                return
            
            total_parts = self.total_parts_var.get()
            cycle_time = self.cycle_time_var.get()
            start_date = self.start_date_var.get()
            start_hour = self.start_hour_var.get()
            start_minute = self.start_minute_var.get()
            
            # Handle intelligent scheduling
            original_machine = machine_id
            original_date = start_date
            original_hour = start_hour
            original_minute = start_minute
            
            if self.find_next_slot_var.get():
                # Find next available slot
                opt_machine, opt_timestamp, opt_date, opt_hour, opt_minute = self._find_next_available_slot(
                    job_name, total_parts, cycle_time
                )
                if opt_machine:
                    machine_id = opt_machine
                    start_date = opt_date
                    start_hour = opt_hour
                    start_minute = opt_minute
            elif self.optimize_schedule_var.get():
                # Optimize production schedule
                opt_machine, opt_timestamp, opt_date, opt_hour, opt_minute = self._optimize_production_schedule(
                    job_name, total_parts, cycle_time
                )
                if opt_machine:
                    machine_id = opt_machine
                    start_date = opt_date
                    start_hour = opt_hour
                    start_minute = opt_minute
            
            # Determine job status and create with JMS integration
            create_jms = self.create_jms_order_var.get() and self.jms_service
            job_status = 'locked' if create_jms else 'active'
            
            # Create the job
            job = self.scheduler_service.create_job_with_parts(
                name=job_name,
                machine_id=machine_id,
                total_parts=total_parts,
                cycle_time=cycle_time,
                start_date=start_date,
                start_hour=start_hour,
                start_minute=start_minute,
                status=job_status
            )
            
            # Build success message
            message = f"Job '{job_name}' created successfully!\n\n"
            message += f"Job ID: {job.job_id}\n"
            message += f"Status: {job_status.upper()}\n"
            message += f"Total Parts: {total_parts}\n"
            message += f"Cycle Time: {cycle_time} min per part\n"
            message += f"Total Time: {total_parts * cycle_time:.1f} minutes\n"
            message += f"Machine: {machine_id}\n"
            
            # Add scheduling information
            if self.find_next_slot_var.get():
                if machine_id != original_machine:
                    message += f"🔍 Intelligent Scheduling: Moved from {original_machine} to {machine_id}\n"
                    # Add tool availability info if we have analysis data
                    if self.analysis_data and 'analysis' in self.analysis_data:
                        analysis = self.analysis_data['analysis']
                        message += f"🔧 Machine has all {len(analysis.tool_numbers)} required tools\n"
                
                scheduled_time = f"{start_date} {start_hour:02d}:{start_minute:02d}"
                original_time = f"{original_date} {original_hour:02d}:{original_minute:02d}"
                if scheduled_time != original_time:
                    message += f"🔍 Optimized Time: {original_time} → {scheduled_time}\n"
                    
                # Add duration fit information
                duration_msg = f"📅 Scheduled for optimal fit: "
                if total_parts > 1:
                    duration_msg += f"Full order ({total_parts} parts) can complete uninterrupted"
                else:
                    duration_msg += "Single part fits in available slot"
                message += duration_msg + "\n"
                
            elif self.optimize_schedule_var.get():
                if machine_id != original_machine:
                    message += f"⚡ Production Optimization: Moved from {original_machine} to {machine_id}\n"
                    # Add tool availability info if we have analysis data
                    if self.analysis_data and 'analysis' in self.analysis_data:
                        analysis = self.analysis_data['analysis']
                        message += f"🔧 Machine has all {len(analysis.tool_numbers)} required tools\n"
                
                scheduled_time = f"{start_date} {start_hour:02d}:{start_minute:02d}"
                original_time = f"{original_date} {original_hour:02d}:{original_minute:02d}"
                if scheduled_time != original_time:
                    message += f"⚡ Optimized Time: {original_time} → {scheduled_time}\n"
            
            message += "\n"
            
            # Transfer to JMS if requested
            jms_success = False
            if create_jms:
                try:
                    message += "Transferring job to JMS...\n"
                    order_id = self.jms_service.sync_job_to_jms(job)
                    message += f"✅ JMS Work Order Created: {order_id}\n"
                    message += f"Job is now LOCKED and managed by JMS\n\n"
                    jms_success = True
                except Exception as e:
                    message += f"❌ JMS Transfer Failed: {str(e)}\n"
                    message += f"Job created locally but not transferred to JMS\n\n"
            
            message += "The job has been added to the scheduler."
            if create_jms and jms_success:
                message += "\nCheck the scheduler tab to see the locked job."
            
            messagebox.showinfo("Job Created", message, parent=self.dialog)
            
            # Trigger UI refresh in scheduler tab
            event_system.publish("job_added", job)
            
            # Close dialog
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create job:\n{str(e)}", parent=self.dialog)