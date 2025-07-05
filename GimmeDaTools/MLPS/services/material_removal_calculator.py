"""
Material Removal Rate Calculator for NC Tool Analyzer
Calculates MRR based on tool information and NC code movements
"""
import re
import math
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass

from .tool_parser import ToolInfo


@dataclass
class CuttingOperation:
    """Single cutting operation data"""
    tool_number: str
    start_position: Dict[str, float]
    end_position: Dict[str, float]
    feed_rate: float
    distance: float
    cutting_time: float
    depth_of_cut: float
    width_of_cut: float
    material_removed: float  # mm³


@dataclass
class ToolMRRResult:
    """Material Removal Rate result for a single tool"""
    tool_number: str
    tool_info: Optional[ToolInfo]
    total_cutting_distance: float
    total_cutting_time: float
    total_material_removed: float
    average_feed_rate: float
    average_depth_of_cut: float
    average_width_of_cut: float
    material_removal_rate: float  # mm³/min
    operations: List[CuttingOperation]
    warnings: List[str]


class MaterialRemovalCalculator:
    """Calculator for Material Removal Rates from NC code"""
    
    def __init__(self):
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        self.current_feedrate = 0
        self.current_tool = None
        self.default_feedrate = 100  # Default feedrate if none specified
        self.rapid_feedrate = 10000  # Rapid traverse rate
        
    def analyze_nc_file_mrr(self, nc_file_path: str) -> Dict[str, ToolMRRResult]:
        """
        Complete MRR analysis for entire NC file
        
        Args:
            nc_file_path: Path to NC file
            
        Returns:
            Dictionary of tool_number -> ToolMRRResult
        """
        from .tool_parser import ToolCommentParser
        
        # Parse tool information
        parser = ToolCommentParser()
        tool_info = parser.extract_all_tool_info(nc_file_path)
        
        # Analyze cutting operations
        cutting_operations = self._analyze_cutting_operations(nc_file_path)
        
        # Calculate MRR for each tool
        mrr_results = {}
        
        for tool_number in set(op.tool_number for op in cutting_operations):
            tool_ops = [op for op in cutting_operations if op.tool_number == tool_number]
            tool_mrr = self._calculate_tool_mrr(
                tool_number, 
                tool_info.get(tool_number), 
                tool_ops
            )
            mrr_results[tool_number] = tool_mrr
            
        return mrr_results
    
    def _analyze_cutting_operations(self, nc_file_path: str) -> List[CuttingOperation]:
        """
        Analyze NC file to extract cutting operations
        
        Args:
            nc_file_path: Path to NC file
            
        Returns:
            List of CuttingOperation objects
        """
        operations = []
        
        try:
            with open(nc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
            self.current_feedrate = self.default_feedrate
            self.current_tool = None
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith(';') or line.startswith('(') or line.startswith('*'):
                    continue
                
                # Process the line
                operation = self._process_cutting_line(line, line_num)
                if operation:
                    operations.append(operation)
        
        except Exception as e:
            print(f"Error analyzing cutting operations: {str(e)}")
        
        return operations
    
    def _process_cutting_line(self, line: str, line_num: int) -> Optional[CuttingOperation]:
        """
        Process a single line for cutting operations
        
        Args:
            line: NC code line
            line_num: Line number for debugging
            
        Returns:
            CuttingOperation if this line represents cutting, None otherwise
        """
        # Tool change
        tool_match = re.search(r'TOOL CALL (\d+)', line)
        if tool_match:
            self.current_tool = tool_match.group(1)
            return None
        
        # Skip if no current tool
        if not self.current_tool:
            return None
        
        # Feedrate
        f_match = re.search(r'F(\d+\.?\d*)', line)
        if f_match:
            self.current_feedrate = float(f_match.group(1))
        
        # Check for rapid movement (FMAX)
        is_rapid = 'FMAX' in line
        if is_rapid:
            return None  # Skip rapid movements for MRR calculation
        
        # Extract coordinates
        new_position = self.current_position.copy()
        has_movement = False
        
        for axis in ['X', 'Y', 'Z']:
            axis_match = re.search(rf'{axis}([+-]?\d+\.?\d*)', line)
            if axis_match:
                new_position[axis] = float(axis_match.group(1))
                has_movement = True
        
        if not has_movement or self.current_feedrate <= 0:
            return None
        
        # Calculate movement distance
        distance = self._calculate_distance(self.current_position, new_position)
        if distance < 0.01:  # Ignore very small movements
            return None
        
        # Calculate cutting time
        cutting_time = (distance / self.current_feedrate) * 60  # Convert to seconds
        
        # Estimate depth and width of cut
        depth_of_cut = abs(new_position['Z'] - self.current_position['Z'])
        width_of_cut = math.sqrt(
            (new_position['X'] - self.current_position['X'])**2 + 
            (new_position['Y'] - self.current_position['Y'])**2
        )
        
        # If no Z movement, assume constant depth based on typical machining
        if depth_of_cut < 0.01:
            depth_of_cut = 1.0  # Default 1mm depth for finishing passes
        
        # If no XY movement, assume slot width equals tool diameter (will be refined later)
        if width_of_cut < 0.01:
            width_of_cut = 6.0  # Default 6mm width, will be updated with actual tool diameter
        
        # Calculate material removed (simplified)
        material_removed = depth_of_cut * width_of_cut * distance
        
        # Create cutting operation
        operation = CuttingOperation(
            tool_number=self.current_tool,
            start_position=self.current_position.copy(),
            end_position=new_position.copy(),
            feed_rate=self.current_feedrate,
            distance=distance,
            cutting_time=cutting_time,
            depth_of_cut=depth_of_cut,
            width_of_cut=width_of_cut,
            material_removed=material_removed
        )
        
        # Update current position
        self.current_position = new_position
        
        return operation
    
    def _calculate_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate 3D distance between two positions"""
        return math.sqrt(
            (pos2['X'] - pos1['X'])**2 +
            (pos2['Y'] - pos1['Y'])**2 +
            (pos2['Z'] - pos1['Z'])**2
        )
    
    def _calculate_tool_mrr(self, tool_number: str, tool_info: Optional[ToolInfo], 
                           operations: List[CuttingOperation]) -> ToolMRRResult:
        """
        Calculate MRR for a specific tool
        
        Args:
            tool_number: Tool number
            tool_info: Tool information from comments
            operations: List of cutting operations for this tool
            
        Returns:
            ToolMRRResult object
        """
        if not operations:
            return ToolMRRResult(
                tool_number=tool_number,
                tool_info=tool_info,
                total_cutting_distance=0,
                total_cutting_time=0,
                total_material_removed=0,
                average_feed_rate=0,
                average_depth_of_cut=0,
                average_width_of_cut=0,
                material_removal_rate=0,
                operations=[],
                warnings=["No cutting operations found"]
            )
        
        # Refine calculations with actual tool diameter if available
        if tool_info and tool_info.diameter:
            operations = self._refine_operations_with_tool_diameter(operations, tool_info.diameter)
        
        # Calculate totals
        total_distance = sum(op.distance for op in operations)
        total_time = sum(op.cutting_time for op in operations)
        total_material = sum(op.material_removed for op in operations)
        
        # Calculate averages
        avg_feed_rate = sum(op.feed_rate for op in operations) / len(operations)
        avg_depth = sum(op.depth_of_cut for op in operations) / len(operations)
        avg_width = sum(op.width_of_cut for op in operations) / len(operations)
        
        # Calculate Material Removal Rate (mm³/min)
        mrr = (total_material / (total_time / 60)) if total_time > 0 else 0
        
        # Generate warnings
        warnings = []
        if not tool_info:
            warnings.append("No tool information found in comments")
        if not tool_info or not tool_info.diameter:
            warnings.append("Tool diameter unknown - using estimates")
        if mrr > 50000:  # Very high MRR might indicate calculation error
            warnings.append("Unusually high MRR - please verify calculations")
        if mrr < 10:  # Very low MRR might indicate finishing operations
            warnings.append("Low MRR - likely finishing operations")
        
        return ToolMRRResult(
            tool_number=tool_number,
            tool_info=tool_info,
            total_cutting_distance=total_distance,
            total_cutting_time=total_time,
            total_material_removed=total_material,
            average_feed_rate=avg_feed_rate,
            average_depth_of_cut=avg_depth,
            average_width_of_cut=avg_width,
            material_removal_rate=mrr,
            operations=operations,
            warnings=warnings
        )
    
    def _refine_operations_with_tool_diameter(self, operations: List[CuttingOperation], 
                                            diameter: float) -> List[CuttingOperation]:
        """
        Refine operation calculations using actual tool diameter
        
        Args:
            operations: List of operations to refine
            diameter: Tool diameter in mm
            
        Returns:
            Updated list of operations
        """
        refined_ops = []
        
        for op in operations:
            # Create a copy
            refined_op = CuttingOperation(
                tool_number=op.tool_number,
                start_position=op.start_position,
                end_position=op.end_position,
                feed_rate=op.feed_rate,
                distance=op.distance,
                cutting_time=op.cutting_time,
                depth_of_cut=op.depth_of_cut,
                width_of_cut=op.width_of_cut,
                material_removed=op.material_removed
            )
            
            # Refine width of cut based on tool diameter
            # For slotting operations (no XY movement), width = diameter
            if refined_op.width_of_cut < 0.01:
                refined_op.width_of_cut = diameter
            # For contouring, width is typically a fraction of diameter
            elif refined_op.width_of_cut > diameter * 2:
                refined_op.width_of_cut = diameter * 0.8  # 80% engagement typical
            
            # Recalculate material removed with refined parameters
            refined_op.material_removed = (refined_op.depth_of_cut * 
                                         refined_op.width_of_cut * 
                                         refined_op.distance)
            
            refined_ops.append(refined_op)
        
        return refined_ops