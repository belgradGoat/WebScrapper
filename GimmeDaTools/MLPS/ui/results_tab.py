"""
Results Tab for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime

from utils.event_system import event_system


class ResultsTab:
    """
    Results tab for the NC Tool Analyzer application
    """
    def __init__(self, parent, analysis_service):
        """
        Initialize the results tab
        
        Args:
            parent: Parent widget
            analysis_service: AnalysisService instance
        """
        self.parent = parent
        self.analysis_service = analysis_service
        
        # Create frame
        self.frame = ttk.Frame(parent)
        
        # Setup UI components
        self.setup_ui()
        
        # Subscribe to events
        self._setup_event_handlers()
        
    def setup_ui(self):
        """Set up the UI components"""
        # Control frame for clear button
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(control_frame, text="Clear Log", command=self.clear_log).pack(side=tk.RIGHT)
        ttk.Label(control_frame, text="Analysis Results Log", font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Initial message
        self.append_log_entry("SYSTEM", "Results log initialized. Perform analysis operations to see detailed results here.\n\n" +
                             "Available operations:\n" +
                             "• Check Machine Compatibility - Tool analysis and machine matching\n" +
                             "• Calculate Cycle Time - Time analysis with operation breakdown\n" +
                             "• Calculate Material Removal Rates - MRR analysis with tool-by-tool details")
        
    def _setup_event_handlers(self):
        """Set up event handlers for tab events"""
        # Update results when analysis is complete
        event_system.subscribe("analysis_complete", self.display_results)
        
        # Add log entries for other operations
        event_system.subscribe("cycle_time_calculated", self.log_cycle_time_results)
        event_system.subscribe("mrr_calculated", self.log_mrr_results)
        
    def append_log_entry(self, operation_type, content):
        """
        Append a timestamped log entry
        
        Args:
            operation_type: Type of operation (e.g., "ANALYSIS", "CYCLE_TIME", "MRR")
            content: Content to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add separator if not the first entry
        current_content = self.results_text.get(1.0, tk.END).strip()
        if current_content and not current_content.endswith("Results log initialized"):
            self.results_text.insert(tk.END, "\n\n" + "="*80 + "\n\n")
        
        # Add timestamped header
        header = f"[{timestamp}] {operation_type}\n" + "-" * 60 + "\n"
        self.results_text.insert(tk.END, header)
        
        # Add content
        self.results_text.insert(tk.END, content)
        
        # Auto-scroll to bottom
        self.results_text.see(tk.END)
        
    def clear_log(self):
        """Clear the results log"""
        self.results_text.delete(1.0, tk.END)
        self.append_log_entry("SYSTEM", "Results log cleared.")
        
    def display_results(self, analysis_result):
        """
        Display analysis results as a log entry
        
        Args:
            analysis_result: AnalysisResult object
        """
        output = []
        output.append(f"NC TOOL ANALYSIS RESULTS")
        output.append(f"File: {analysis_result.file_name}")
        output.append(f"Tools Required: {analysis_result.total_tools}")
        output.append(f"F-Value Errors: {len(analysis_result.f_value_errors)}")
        
        # Add download info if available
        if analysis_result.download_info:
            output.append(f"Tool Data: {analysis_result.download_info}")
        
        output.append("")
        
        # Add debug information at the top
        if analysis_result.debug_info:
            output.extend(analysis_result.debug_info)
            output.append("")
            output.append("=" * 60)
            output.append("")
        
        # Stock dimensions
        if analysis_result.dimensions:
            dim = analysis_result.dimensions
            output.append("STOCK DIMENSIONS:")
            output.append(f"Width: {dim.width:.2f} mm")
            output.append(f"Height: {dim.height:.2f} mm") 
            output.append(f"Depth: {dim.depth:.2f} mm")
            output.append("")
        
        # Preset values
        if analysis_result.preset_values:
            output.append("PRESET VALUES:")
            for preset in analysis_result.preset_values:
                output.append(f"Preset: {preset}")
            output.append("")
        
        # Tools needed with life information
        output.append("TOOLS NEEDED IN SEQUENCE ORDER:")
        output.append("-" * 40)
        for tool in analysis_result.tool_numbers:
            comp_info = analysis_result.cutter_comp_info.get(tool, 'Cutter Comp: Off')
            output.append(f"T{tool}")
            output.append(f"{comp_info}")
            
            # Add tool life information if available from any machine
            tool_life_found = False
            for machine in analysis_result.machine_analysis:
                machine_obj = self.analysis_service.machine_service.get_machine(machine.machine_id)
                if not machine_obj:
                    continue
                    
                tool_life_data = machine_obj.tool_life_data
                if tool in tool_life_data:
                    life_info = tool_life_data[tool]
                    current = life_info.get('current_time', 0)
                    max_time = life_info.get('max_time')
                    percentage = life_info.get('usage_percentage')
                    
                    if max_time is not None and percentage is not None:
                        output.append(f"Tool Life: {current:.1f}/{max_time:.1f} min ({percentage:.1f}% used) - {machine.machine_id}")
                    else:
                        output.append(f"Tool Life: {current:.1f} min used - {machine.machine_id}")
                    tool_life_found = True
                    break
            
            if not tool_life_found:
                output.append("Tool Life: No data available")
            
            output.append("-" * 20)
        output.append("")
        
        # Machine analysis
        output.append("MACHINE COMPATIBILITY ANALYSIS:")
        output.append("=" * 40)
        
        for machine in analysis_result.machine_analysis:
            output.append(f"\n{machine.machine_name} ({machine.machine_id})")
            output.append(f"Type: {machine.machine_type}")
            output.append(f"Location: {machine.location}")
            output.append(f"Match: {machine.match_percentage}% ({len(machine.matching_tools)}/{analysis_result.total_tools} tools)")
            
            # Enhanced tool status display
            available_count = machine.total_physical_tools
            locked_count = machine.total_locked_tools
            if locked_count > 0:
                output.append(f"Tool Status: {available_count} Available, {locked_count} Locked/Broken")
            else:
                output.append(f"Physical Tools Available: {available_count}")
            
            output.append(f"Last Updated: {machine.last_updated}")
            
            # Show tool status for required tools
            if machine.missing_tools:
                output.append(f"❌ Missing Tools: T{', T'.join(machine.missing_tools)}")
            
            if machine.locked_required_tools:
                output.append(f"🔒 Required Tools Locked/Broken: T{', T'.join(machine.locked_required_tools)}")
            
            if not machine.missing_tools and not machine.locked_required_tools:
                output.append("✅ All required tools are available!")
            elif not machine.missing_tools and machine.locked_required_tools:
                output.append("⚠️ All tools physically present but some are locked/broken!")
            
            # Show tool life information for available required tools
            machine_obj = self.analysis_service.machine_service.get_machine(machine.machine_id)
            if machine_obj:
                tool_life_data = machine_obj.tool_life_data
                available_required_tools = [t for t in analysis_result.tool_numbers
                                         if t in machine.matching_tools and t in tool_life_data]
                
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
        if analysis_result.f_value_errors:
            output.append("\nF-VALUE ERRORS (>80000):")
            for error in analysis_result.f_value_errors:
                output.append(f"Line {error.line}: F{error.value} - {error.text}")
        
        # Use the log entry method instead of direct insertion
        self.append_log_entry("MACHINE COMPATIBILITY ANALYSIS", "\n".join(output))
    
    def log_cycle_time_results(self, data):
        """
        Log cycle time calculation results
        
        Args:
            data: Dictionary containing cycle_data and analysis information
        """
        cycle_data = data['cycle_data']
        analysis = data.get('analysis')
        
        output = []
        if analysis:
            output.append(f"File: {analysis.file_name}")
        output.append(f"Total Cycle Time: {cycle_data['total_time_formatted']}")
        output.append(f"Total Cycle Time (seconds): {cycle_data['total_time']:.2f}")
        output.append("")
        
        # Operation breakdown
        output.append("TIME BREAKDOWN BY OPERATION:")
        output.append("-" * 40)
        for op_type, time_seconds in cycle_data['operation_times'].items():
            if time_seconds > 0:
                count = cycle_data['operation_counts'][op_type]
                formatted_time = self._format_time_simple(time_seconds)
                percentage = (time_seconds / cycle_data['total_time']) * 100 if cycle_data['total_time'] > 0 else 0
                output.append(f"{op_type.title():12}: {formatted_time:>12} ({percentage:5.1f}%) - {count} operations")
        output.append("")
        
        # Tool information
        if analysis:
            output.append("TOOL INFORMATION:")
            output.append("-" * 40)
            output.append(f"Total Tools Used: {analysis.total_tools}")
            output.append(f"Tools: T{', T'.join(analysis.tool_numbers)}")
            output.append("")
        
        # Movement analysis
        rapid_moves = [m for m in cycle_data['movements'] if m['type'] == 'rapid']
        feed_moves = [m for m in cycle_data['movements'] if m['type'] == 'feed']
        
        if rapid_moves or feed_moves:
            output.append("MOVEMENT ANALYSIS:")
            output.append("-" * 40)
            
            if rapid_moves:
                total_rapid_distance = sum(m['distance'] for m in rapid_moves)
                avg_rapid_feedrate = sum(m['feedrate'] for m in rapid_moves) / len(rapid_moves)
                output.append(f"Rapid Movements: {len(rapid_moves)} moves")
                output.append(f"Total Rapid Distance: {total_rapid_distance:.2f} mm")
                output.append(f"Average Rapid Rate: {avg_rapid_feedrate:.0f} mm/min")
                output.append("")
            
            if feed_moves:
                total_feed_distance = sum(m['distance'] for m in feed_moves)
                avg_feedrate = sum(m['feedrate'] for m in feed_moves) / len(feed_moves)
                output.append(f"Feed Movements: {len(feed_moves)} moves")
                output.append(f"Total Feed Distance: {total_feed_distance:.2f} mm")
                output.append(f"Average Feed Rate: {avg_feedrate:.0f} mm/min")
                output.append("")
        
        # Summary
        output.append("SUMMARY:")
        output.append("-" * 40)
        output.append(f"• Total operations: {sum(cycle_data['operation_counts'].values())}")
        output.append(f"• Tool changes: {cycle_data['operation_counts']['tool_change']}")
        output.append(f"• Feed movements: {cycle_data['operation_counts']['feed']}")
        output.append(f"• Rapid movements: {cycle_data['operation_counts']['rapid']}")
        if cycle_data['operation_counts']['dwell'] > 0:
            output.append(f"• Dwell operations: {cycle_data['operation_counts']['dwell']}")
        
        self.append_log_entry("CYCLE TIME ANALYSIS", "\n".join(output))
    
    def log_mrr_results(self, data):
        """
        Log material removal rate calculation results
        
        Args:
            data: Dictionary containing mrr_results and file_name
        """
        mrr_results = data['mrr_results']
        file_name = data['file_name']
        
        if not mrr_results:
            self.append_log_entry("MATERIAL REMOVAL RATE ANALYSIS",
                                f"File: {file_name}\nNo tools with material removal data found.")
            return
        
        output = []
        output.append(f"File: {file_name}")
        output.append(f"Tools Analyzed: {len(mrr_results)}")
        output.append("")
        
        # Calculate summary statistics
        total_material_removed_mm3 = sum(result.total_material_removed_mm3 for result in mrr_results.values())
        total_material_removed_m3 = sum(result.total_material_removed_m3 for result in mrr_results.values())
        tools_with_data = [r for r in mrr_results.values() if r.total_material_removed_mm3 > 0]
        
        if tools_with_data:
            avg_mrr_mm3 = sum(r.average_mrr_mm3_per_min for r in tools_with_data) / len(tools_with_data)
            avg_mrr_m3 = sum(r.average_mrr_m3_per_min for r in tools_with_data) / len(tools_with_data)
            max_mrr_tool = max(tools_with_data, key=lambda x: x.average_mrr_mm3_per_min)
            min_mrr_tool = min(tools_with_data, key=lambda x: x.average_mrr_mm3_per_min)
        
        # Tool analysis results (summarized for log)
        output.append("TOOL ANALYSIS SUMMARY:")
        output.append("-" * 40)
        
        for tool_num, result in sorted(mrr_results.items()):
            output.append(f"Tool T{result.tool_number}:")
            
            if result.tool_info and result.tool_info.diameter:
                output.append(f"  • Type: {result.tool_info.tool_type_name or 'Unknown'} ({result.tool_info.diameter:.2f}mm)")
            else:
                output.append(f"  • Type: Unknown (no tool data)")
                
            if result.total_cutting_distance > 0:
                output.append(f"  • Cutting Distance: {result.total_cutting_distance:.1f} mm")
                output.append(f"  • Feed Rate: {result.average_feed_rate:.0f} mm/min")
                output.append(f"  • MRR: {result.average_mrr_mm3_per_min:.0f} mm³/min ({result.average_mrr_m3_per_min:.6f} m³/min)")
                output.append(f"  • Material Removed: {result.total_material_removed_mm3:.0f} mm³")
                output.append(f"  • Cutting Time: {result.total_cutting_time:.1f} min")
                
                if result.machining_strategies:
                    strategies = [f"{s}({c})" for s, c in result.machining_strategies.items()]
                    output.append(f"  • Strategies: {', '.join(strategies)}")
            else:
                output.append(f"  • No cutting operations detected")
            output.append("")
        
        # Summary section
        output.append("OVERALL SUMMARY:")
        output.append("-" * 40)
        output.append(f"• Total Material Removed: {total_material_removed_mm3:.0f} mm³ ({total_material_removed_m3:.9f} m³)")
        
        if tools_with_data:
            output.append(f"• Average MRR: {avg_mrr_mm3:.0f} mm³/min ({avg_mrr_m3:.6f} m³/min)")
            output.append(f"• Most Efficient: T{max_mrr_tool.tool_number} ({max_mrr_tool.average_mrr_mm3_per_min:.0f} mm³/min)")
            output.append(f"• Least Efficient: T{min_mrr_tool.tool_number} ({min_mrr_tool.average_mrr_mm3_per_min:.0f} mm³/min)")
        else:
            output.append("• No tools with cutting operations found")
        
        self.append_log_entry("MATERIAL REMOVAL RATE ANALYSIS", "\n".join(output))
    
    def _format_time_simple(self, seconds):
        """Format time in a simple format for the report"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}min"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"