"""
Analysis Service for NC Tool Analyzer
Handles NC file analysis and machine compatibility checks
"""
import os
import re
from typing import Dict, List, Any, Optional, Tuple

from models.machine import Machine
from models.analysis_result import AnalysisResult, FValueError, StockDimensions, MachineCompatibility
from utils.event_system import event_system


class AnalysisService:
    """
    Service for analyzing NC files and checking machine compatibility
    """
    def __init__(self, machine_service):
        """
        Initialize the analysis service
        
        Args:
            machine_service: MachineService instance for accessing machine data
        """
        self.machine_service = machine_service
        self.current_analysis: Optional[AnalysisResult] = None
        
    def analyze_nc_file(self, file_path: str, refresh_tools: bool = False) -> AnalysisResult:
        """
        Analyze an NC file and check machine compatibility
        
        Args:
            file_path: Path to the NC file to analyze
            refresh_tools: Whether to refresh tool data from machines first
            
        Returns:
            AnalysisResult object with analysis results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"NC file not found: {file_path}")
        
        # Optionally refresh tool data from machines
        download_info = None
        if refresh_tools:
            success_count, total_count = self._refresh_all_machines()
            download_info = f"Tool data refreshed from {success_count}/{total_count} machines"
        else:
            download_info = "Using existing tool data (not refreshed)"
        
        # Parse NC file
        file_name = os.path.basename(file_path)
        tool_numbers, cutter_comp_info, preset_values, f_value_errors, dimensions = self._parse_nc_file(file_path)
        
        # Analyze machine compatibility
        machine_analysis = self._analyze_machine_compatibility(tool_numbers)
        
        # Create analysis result
        self.current_analysis = AnalysisResult(
            file_name=file_name,
            tool_numbers=tool_numbers,
            cutter_comp_info=cutter_comp_info,
            preset_values=preset_values,
            f_value_errors=f_value_errors,
            dimensions=dimensions,
            machine_analysis=machine_analysis,
            download_info=download_info
        )
        
        # Notify listeners that analysis is complete
        event_system.publish("analysis_complete", self.current_analysis)
        
        return self.current_analysis
    
    def _refresh_all_machines(self) -> Tuple[int, int]:
        """
        Refresh tool data from all machines
        
        Returns:
            Tuple of (success_count, total_count)
        """
        machines = self.machine_service.get_all_machines()
        success_count = 0
        total_count = len(machines)
        
        for machine_id in machines:
            success, _ = self.machine_service.download_from_machine(machine_id)
            if success:
                success_count += 1
                
        return success_count, total_count
    
    def _parse_nc_file(self, file_path: str) -> Tuple[List[str], Dict[str, str], List[float], List[FValueError], Optional[StockDimensions]]:
        """
        Parse an NC file for tool calls, cutter compensation, preset values, F-value errors, and stock dimensions
        
        Args:
            file_path: Path to the NC file to parse
            
        Returns:
            Tuple of (tool_numbers, cutter_comp_info, preset_values, f_value_errors, dimensions)
        """
        tool_numbers = []
        cutter_comp_info = {}
        preset_values = []
        f_value_errors = []
        blk_form_data = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        current_tool_number = None
        
        for i, line in enumerate(lines, 1):
            # Check for TOOL CALL
            tool_call_match = re.search(r'TOOL CALL (\d+)', line)
            if tool_call_match:
                current_tool_number = tool_call_match.group(1)
                if current_tool_number not in tool_numbers:
                    tool_numbers.append(current_tool_number)
                    print(f"NC File - Found tool call: {current_tool_number}")
                
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
                        f_value_errors.append(FValueError(
                            line=i,
                            value=f_value,
                            text=line.strip()
                        ))
                except ValueError:
                    pass
        
        # Calculate stock dimensions
        dimensions = None
        if len(blk_form_data) >= 2:
            width = abs(blk_form_data[1]['x'] - blk_form_data[0]['x'])
            height = abs(blk_form_data[1]['y'] - blk_form_data[0]['y'])
            depth = abs(blk_form_data[1]['z'] - blk_form_data[0]['z'])
            dimensions = StockDimensions(width=width, height=height, depth=depth)
        
        # Sort tool numbers
        sorted_tool_numbers = sorted(tool_numbers, key=lambda x: int(x) if x.isdigit() else 999999)
        
        return sorted_tool_numbers, cutter_comp_info, preset_values, f_value_errors, dimensions
    
    def _analyze_machine_compatibility(self, tool_numbers: List[str]) -> List[MachineCompatibility]:
        """
        Analyze machine compatibility with the required tools
        
        Args:
            tool_numbers: List of tool numbers required by the NC file
            
        Returns:
            List of MachineCompatibility objects
        """
        machine_analysis = []
        machines = self.machine_service.get_all_machines()
        
        for machine_id, machine in machines.items():
            physical_tools = machine.physical_tools
            locked_tools = machine.locked_tools
            
            # Check each required tool individually
            matching_tools = []
            missing_tools = []
            locked_required_tools = []
            
            for tool in tool_numbers:
                if tool in physical_tools:
                    matching_tools.append(tool)
                elif tool in locked_tools:
                    locked_required_tools.append(tool)
                else:
                    # Check if it exists as different type (string vs int)
                    str_tool = str(tool)
                    int_tool = int(tool) if str(tool).isdigit() else None
                    
                    if str_tool in physical_tools:
                        matching_tools.append(tool)
                    elif int_tool and int_tool in physical_tools:
                        matching_tools.append(tool)
                    elif str_tool in locked_tools:
                        locked_required_tools.append(tool)
                    elif int_tool and int_tool in locked_tools:
                        locked_required_tools.append(tool)
                    else:
                        missing_tools.append(tool)
            
            # Calculate match percentage
            match_percentage = (len(matching_tools) / len(tool_numbers) * 100) if tool_numbers else 0
            
            # Create machine compatibility object
            compatibility = MachineCompatibility(
                machine_id=machine_id,
                machine_name=machine.name,
                machine_type=machine.machine_type,
                location=machine.location,
                matching_tools=matching_tools,
                missing_tools=missing_tools,
                locked_required_tools=locked_required_tools,
                match_percentage=round(match_percentage),
                total_physical_tools=len(physical_tools),
                total_locked_tools=len(locked_tools),
                last_updated=machine.last_updated or "Never"
            )
            
            machine_analysis.append(compatibility)
        
        # Sort by match percentage (highest first)
        machine_analysis.sort(key=lambda x: x.match_percentage, reverse=True)
        
        return machine_analysis