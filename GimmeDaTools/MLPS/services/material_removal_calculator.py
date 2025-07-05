"""
Material Removal Rate Calculator for NC Tool Analyzer
Calculates MRR based on proper machining formulas: MRR = DOC × WOC × F
"""
import re
import math
from typing import Dict, List, Optional, NamedTuple, Tuple
from dataclasses import dataclass

from .tool_parser import ToolInfo


@dataclass
class StockBoundary:
    """Stock material boundaries"""
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_top: float  # Top surface of stock


@dataclass
class CuttingMove:
    """Single cutting move with MRR calculation"""
    tool_number: str
    start_pos: Dict[str, float]
    end_pos: Dict[str, float]
    feed_rate: float  # mm/min
    distance: float  # mm
    depth_of_cut: float  # mm (DOC)
    width_of_cut: float  # mm (WOC)
    mrr: float  # mm³/min for this move
    material_removed: float  # mm³ for this move
    cutting_time: float  # minutes
    move_type: str  # 'slotting', 'pocketing', 'profiling', 'drilling'


@dataclass
class ToolMRRResult:
    """Material Removal Rate result for a single tool"""
    tool_number: str
    tool_info: Optional[ToolInfo]
    cutting_moves: List[CuttingMove]
    total_cutting_distance: float  # mm
    total_cutting_time: float  # minutes
    total_material_removed_mm3: float  # mm³
    total_material_removed_m3: float  # m³ (converted)
    average_mrr_mm3_per_min: float  # mm³/min
    average_mrr_m3_per_min: float  # m³/min (converted)
    average_feed_rate: float  # mm/min
    average_doc: float  # mm
    average_woc: float  # mm
    machining_strategies: Dict[str, int]  # Count of each strategy type
    warnings: List[str]


class MaterialRemovalCalculator:
    """Calculator for Material Removal Rates using proper machining formulas"""
    
    def __init__(self):
        self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
        self.previous_position = {'X': 0, 'Y': 0, 'Z': 0}
        self.current_feedrate = 100  # Default feedrate mm/min
        self.current_tool = None
        self.stock_boundary = None
        self.rapid_feedrate = 10000
        self.z_levels = {}  # Track Z levels for each tool to calculate DOC
        
    def analyze_nc_file_mrr(self, nc_file_path: str) -> Dict[str, ToolMRRResult]:
        """
        Complete MRR analysis for entire NC file using proper MRR = DOC × WOC × F formula
        
        Args:
            nc_file_path: Path to NC file
            
        Returns:
            Dictionary of tool_number -> ToolMRRResult
        """
        from .tool_parser import ToolCommentParser
        
        # Parse tool information
        parser = ToolCommentParser()
        tool_info = parser.extract_all_tool_info(nc_file_path)
        
        # Extract stock boundaries and analyze cutting moves
        self.stock_boundary = self._extract_stock_boundary(nc_file_path)
        cutting_moves = self._analyze_cutting_moves(nc_file_path, tool_info)
        
        # Calculate MRR for each tool
        mrr_results = {}
        
        # Group moves by tool
        tools_moves = {}
        for move in cutting_moves:
            if move.tool_number not in tools_moves:
                tools_moves[move.tool_number] = []
            tools_moves[move.tool_number].append(move)
        
        # Calculate results for each tool
        for tool_number, moves in tools_moves.items():
            tool_mrr = self._calculate_tool_mrr_result(
                tool_number, 
                tool_info.get(tool_number), 
                moves
            )
            mrr_results[tool_number] = tool_mrr
            
        return mrr_results
    
    def _extract_stock_boundary(self, nc_file_path: str) -> Optional[StockBoundary]:
        """Extract stock boundary information from BLK FORM commands"""
        try:
            with open(nc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            blk_forms = []
            for line in lines:
                blk_match = re.search(r'BLK FORM \d+\.?\d* (?:Z )?X([-+]?\d+\.?\d*) Y([-+]?\d+\.?\d*) Z([-+]?\d+\.?\d*)', line)
                if blk_match:
                    blk_forms.append({
                        'x': float(blk_match.group(1)),
                        'y': float(blk_match.group(2)),
                        'z': float(blk_match.group(3))
                    })
            
            if len(blk_forms) >= 2:
                # Calculate boundaries
                x_coords = [b['x'] for b in blk_forms]
                y_coords = [b['y'] for b in blk_forms]
                z_coords = [b['z'] for b in blk_forms]
                
                return StockBoundary(
                    x_min=min(x_coords),
                    x_max=max(x_coords),
                    y_min=min(y_coords),
                    y_max=max(y_coords),
                    z_top=max(z_coords)  # Top surface
                )
        except Exception as e:
            print(f"Error extracting stock boundary: {e}")
        
        return None
    
    def _analyze_cutting_moves(self, nc_file_path: str, tool_info: Dict[str, ToolInfo]) -> List[CuttingMove]:
        """Analyze NC file to extract cutting moves with proper DOC/WOC calculations"""
        moves = []
        
        try:
            with open(nc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            self.current_position = {'X': 0, 'Y': 0, 'Z': 0}
            self.current_feedrate = 100
            self.current_tool = None
            self.z_levels = {}
            
            # Track previous positions for stepover calculation
            tool_paths = {}  # tool_number -> list of XY positions
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith(';') or line.startswith('(') or line.startswith('*'):
                    continue
                
                # Tool change
                tool_match = re.search(r'TOOL CALL (\d+)', line)
                if tool_match:
                    self.current_tool = tool_match.group(1)
                    if self.current_tool not in tool_paths:
                        tool_paths[self.current_tool] = []
                    if self.current_tool not in self.z_levels:
                        self.z_levels[self.current_tool] = []
                    continue
                
                if not self.current_tool:
                    continue
                
                # Update feed rate
                f_match = re.search(r'F(\d+\.?\d*)', line)
                if f_match:
                    self.current_feedrate = float(f_match.group(1))
                
                # Skip rapid moves
                if 'FMAX' in line:
                    self._update_position(line)
                    continue
                
                # Process cutting moves (L, G01, G02, G03)
                if self._is_cutting_move(line):
                    move = self._process_cutting_move(line, tool_info, tool_paths)
                    if move:
                        moves.append(move)
        
        except Exception as e:
            print(f"Error analyzing cutting moves: {e}")
        
        return moves
    
    def _is_cutting_move(self, line: str) -> bool:
        """Check if line represents a cutting move"""
        cutting_commands = ['L ', 'G01', 'G1 ', 'G02', 'G2 ', 'G03', 'G3 ']
        return any(line.startswith(cmd) or f' {cmd}' in line for cmd in cutting_commands)
    
    def _process_cutting_move(self, line: str, tool_info: Dict[str, ToolInfo], 
                             tool_paths: Dict[str, List]) -> Optional[CuttingMove]:
        """Process a single cutting move and calculate DOC, WOC, and MRR"""
        
        # Store previous position
        self.previous_position = self.current_position.copy()
        
        # Update current position
        new_position = self._update_position(line)
        if not new_position:
            return None
        
        # Calculate distance
        distance = self._calculate_3d_distance(self.previous_position, self.current_position)
        if distance < 0.01:  # Skip very small moves
            return None
        
        # Get tool information
        tool_info_obj = tool_info.get(self.current_tool)
        tool_diameter = tool_info_obj.diameter if tool_info_obj else 6.0  # Default 6mm
        
        # Calculate Depth of Cut (DOC)
        doc = self._calculate_doc(self.previous_position['Z'], self.current_position['Z'])
        
        # Calculate Width of Cut (WOC) and determine machining strategy
        woc, strategy = self._calculate_woc_and_strategy(
            self.previous_position, self.current_position, 
            tool_diameter, tool_paths[self.current_tool]
        )
        
        # Add current position to tool path for future WOC calculations
        tool_paths[self.current_tool].append({
            'x': self.current_position['X'],
            'y': self.current_position['Y'],
            'z': self.current_position['Z']
        })
        
        # Calculate MRR using proper formula: MRR = DOC × WOC × F
        mrr_mm3_per_min = doc * woc * self.current_feedrate
        
        # Calculate cutting time (minutes)
        cutting_time = distance / self.current_feedrate
        
        # Calculate material removed for this move (mm³)
        material_removed = mrr_mm3_per_min * cutting_time
        
        return CuttingMove(
            tool_number=self.current_tool,
            start_pos=self.previous_position.copy(),
            end_pos=self.current_position.copy(),
            feed_rate=self.current_feedrate,
            distance=distance,
            depth_of_cut=doc,
            width_of_cut=woc,
            mrr=mrr_mm3_per_min,
            material_removed=material_removed,
            cutting_time=cutting_time,
            move_type=strategy
        )
    
    def _update_position(self, line: str) -> bool:
        """Update current position from NC line"""
        updated = False
        
        for axis in ['X', 'Y', 'Z']:
            match = re.search(rf'{axis}([+-]?\d+\.?\d*)', line)
            if match:
                self.current_position[axis] = float(match.group(1))
                updated = True
        
        return updated
    
    def _calculate_3d_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """Calculate 3D distance between positions"""
        return math.sqrt(
            (pos2['X'] - pos1['X'])**2 +
            (pos2['Y'] - pos1['Y'])**2 +
            (pos2['Z'] - pos1['Z'])**2
        )
    
    def _calculate_doc(self, z_start: float, z_end: float) -> float:
        """
        Calculate Depth of Cut (DOC)
        
        For machining operations, DOC is the depth of material being removed
        """
        z_change = abs(z_end - z_start)
        
        # If there's Z movement, that's the DOC
        if z_change > 0.01:
            return z_change
        
        # For constant Z moves (like in pocketing), use typical DOC
        # This would ideally be calculated from the actual cutting depth relative to stock
        if self.stock_boundary and z_end < self.stock_boundary.z_top:
            # Calculate depth below stock surface
            depth_below_stock = self.stock_boundary.z_top - z_end
            return min(depth_below_stock, 2.0)  # Cap at reasonable DOC
        
        # Default DOC for finishing passes
        return 0.5
    
    def _calculate_woc_and_strategy(self, start_pos: Dict[str, float], end_pos: Dict[str, float],
                                   tool_diameter: float, tool_path: List[Dict]) -> Tuple[float, str]:
        """
        Calculate Width of Cut (WOC) and determine machining strategy
        
        Returns: (WOC in mm, strategy name)
        """
        xy_distance = math.sqrt(
            (end_pos['X'] - start_pos['X'])**2 +
            (end_pos['Y'] - start_pos['Y'])**2
        )
        
        z_change = abs(end_pos['Z'] - start_pos['Z'])
        
        # Drilling operation - vertical movement only
        if xy_distance < 0.01 and z_change > 0.1:
            return tool_diameter, 'drilling'
        
        # No XY movement - likely a mistake or setup move
        if xy_distance < 0.01:
            return 0.0, 'non_cutting'
        
        # Analyze toolpath pattern to determine strategy
        if len(tool_path) >= 2:
            # Calculate stepover by finding nearest parallel toolpath
            stepover = self._calculate_stepover(start_pos, tool_path, tool_diameter)
            
            if stepover < tool_diameter * 1.1:  # Close to full engagement
                # Slotting operation
                return tool_diameter, 'slotting'
            elif stepover > 0:
                # Pocketing/facing with calculated stepover
                return stepover, 'pocketing'
        
        # Default to profiling with typical radial engagement
        # For profiling, WOC is typically 10-50% of tool diameter
        radial_engagement = tool_diameter * 0.3  # 30% engagement typical for profiling
        return radial_engagement, 'profiling'
    
    def _calculate_stepover(self, current_pos: Dict[str, float], 
                           tool_path: List[Dict], tool_diameter: float) -> float:
        """Calculate stepover distance by finding nearest parallel toolpath"""
        if len(tool_path) < 2:
            return 0.0
        
        current_xy = (current_pos['X'], current_pos['Y'])
        min_distance = float('inf')
        
        # Look for parallel toolpaths at similar Z levels
        current_z = current_pos['Z']
        
        for path_pos in tool_path:
            # Only consider positions at similar Z levels
            if abs(path_pos['z'] - current_z) < 0.5:
                distance = math.sqrt(
                    (path_pos['x'] - current_xy[0])**2 +
                    (path_pos['y'] - current_xy[1])**2
                )
                if 0.1 < distance < min_distance:  # Ignore very close points
                    min_distance = distance
        
        return min_distance if min_distance != float('inf') else tool_diameter * 0.5
    
    def _calculate_tool_mrr_result(self, tool_number: str, tool_info: Optional[ToolInfo],
                                  moves: List[CuttingMove]) -> ToolMRRResult:
        """Calculate comprehensive MRR results for a tool"""
        
        if not moves:
            return ToolMRRResult(
                tool_number=tool_number,
                tool_info=tool_info,
                cutting_moves=[],
                total_cutting_distance=0,
                total_cutting_time=0,
                total_material_removed_mm3=0,
                total_material_removed_m3=0,
                average_mrr_mm3_per_min=0,
                average_mrr_m3_per_min=0,
                average_feed_rate=0,
                average_doc=0,
                average_woc=0,
                machining_strategies={},
                warnings=["No cutting moves found"]
            )
        
        # Filter out non-cutting moves
        cutting_moves = [m for m in moves if m.move_type != 'non_cutting' and m.material_removed > 0]
        
        if not cutting_moves:
            return ToolMRRResult(
                tool_number=tool_number,
                tool_info=tool_info,
                cutting_moves=moves,
                total_cutting_distance=sum(m.distance for m in moves),
                total_cutting_time=sum(m.cutting_time for m in moves),
                total_material_removed_mm3=0,
                total_material_removed_m3=0,
                average_mrr_mm3_per_min=0,
                average_mrr_m3_per_min=0,
                average_feed_rate=sum(m.feed_rate for m in moves) / len(moves),
                average_doc=0,
                average_woc=0,
                machining_strategies={},
                warnings=["No material removal detected"]
            )
        
        # Calculate totals
        total_distance = sum(m.distance for m in cutting_moves)
        total_time = sum(m.cutting_time for m in cutting_moves)
        total_material_mm3 = sum(m.material_removed for m in cutting_moves)
        
        # Convert to cubic meters
        total_material_m3 = total_material_mm3 / (1000**3)  # mm³ to m³
        
        # Calculate averages
        avg_feed = sum(m.feed_rate for m in cutting_moves) / len(cutting_moves)
        avg_doc = sum(m.depth_of_cut for m in cutting_moves) / len(cutting_moves)
        avg_woc = sum(m.width_of_cut for m in cutting_moves) / len(cutting_moves)
        
        # Calculate average MRR
        avg_mrr_mm3 = total_material_mm3 / total_time if total_time > 0 else 0
        avg_mrr_m3 = total_material_m3 / (total_time / 60) if total_time > 0 else 0  # m³/hour
        
        # Count machining strategies
        strategies = {}
        for move in cutting_moves:
            strategies[move.move_type] = strategies.get(move.move_type, 0) + 1
        
        # Generate warnings
        warnings = []
        if not tool_info:
            warnings.append("No tool information found - using default diameter")
        if avg_mrr_mm3 > 100000:
            warnings.append("Very high MRR - verify calculations")
        if avg_mrr_mm3 < 10:
            warnings.append("Very low MRR - likely finishing operations")
        
        return ToolMRRResult(
            tool_number=tool_number,
            tool_info=tool_info,
            cutting_moves=cutting_moves,
            total_cutting_distance=total_distance,
            total_cutting_time=total_time,
            total_material_removed_mm3=total_material_mm3,
            total_material_removed_m3=total_material_m3,
            average_mrr_mm3_per_min=avg_mrr_mm3,
            average_mrr_m3_per_min=avg_mrr_m3,
            average_feed_rate=avg_feed,
            average_doc=avg_doc,
            average_woc=avg_woc,
            machining_strategies=strategies,
            warnings=warnings
        )