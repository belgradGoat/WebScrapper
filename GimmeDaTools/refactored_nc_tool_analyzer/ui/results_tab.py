"""
Results Tab for NC Tool Analyzer
"""
import tkinter as tk
from tkinter import ttk, scrolledtext

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
        # Results display
        self.results_text = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, font=('Courier', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial message
        self.results_text.insert(tk.END, "Analyze an NC file to see detailed results here.\n\n" +
                                "The results will include:\n" +
                                "• Tool sequence and cutter compensation information\n" +
                                "• Stock dimensions from the NC file\n" +
                                "• Preset values found in the NC file\n" +
                                "• Machine compatibility analysis\n" +
                                "• Tool life information\n" +
                                "• F-value errors (values > 80000)")
        
    def _setup_event_handlers(self):
        """Set up event handlers for tab events"""
        # Update results when analysis is complete
        event_system.subscribe("analysis_complete", self.display_results)
        
    def display_results(self, analysis_result):
        """
        Display analysis results
        
        Args:
            analysis_result: AnalysisResult object
        """
        self.results_text.delete(1.0, tk.END)
        
        output = []
        output.append("=" * 60)
        output.append(f"NC TOOL ANALYSIS RESULTS")
        output.append("=" * 60)
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
        
        self.results_text.insert(tk.END, "\n".join(output))