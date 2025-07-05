"""
Tool Comment Parser for NC Tool Analyzer
Parses tool information from NC file comments in various formats
"""
import re
from typing import Dict, Optional, NamedTuple
from dataclasses import dataclass


@dataclass
class ToolInfo:
    """Tool information extracted from comments"""
    tool_number: str
    tool_type: str = None
    tool_type_name: str = None
    diameter: float = None
    tool_holder: str = None
    flute_length: float = None
    stickout: float = None
    corner_radius: float = None
    material_code: str = None
    flute_count: int = None
    original_comment: str = None


class ToolCommentParser:
    """Parser for extracting tool information from NC file comments"""
    
    def __init__(self):
        self.tool_type_mapping = {
            'SEM': 'Square End Mill',
            'BAL': 'Ball End Mill', 
            'CHM': 'Chamfer',
            'CHE': 'Lollipop End Mill',
            'DRL': 'Drill',
            'TAP': 'Tap',
            'REM': 'Reamer',
            'BOR': 'Boring Tool',
            'FLY': 'Fly Cutter'
        }
    
    def parse_tool_comment(self, comment_line: str, tool_number: str) -> Optional[ToolInfo]:
        """
        Parse a single tool comment line
        
        Expected formats:
        - SEM_06.35_P15-120_L19O25_0.00AL3 T9
        - DRL_03.00_L50_HSS T12
        - Any format containing diameter information
        
        Args:
            comment_line: The comment line to parse
            tool_number: Associated tool number
            
        Returns:
            ToolInfo object or None if parsing fails
        """
        if not comment_line or not tool_number:
            return None
            
        try:
            tool_info = ToolInfo(tool_number=tool_number, original_comment=comment_line.strip())
            
            # Try to parse the structured format first
            if self._parse_structured_format(comment_line, tool_info):
                return tool_info
            
            # Fall back to pattern-based diameter extraction
            if self._extract_diameter_patterns(comment_line, tool_info):
                return tool_info
                
            return None
            
        except Exception as e:
            print(f"Error parsing tool comment for T{tool_number}: {str(e)}")
            return None
    
    def _parse_structured_format(self, comment: str, tool_info: ToolInfo) -> bool:
        """
        Parse structured format: SEM_06.35_P15-120_L19O25_0.00AL3
        
        Args:
            comment: Comment string to parse
            tool_info: ToolInfo object to populate
            
        Returns:
            True if successfully parsed, False otherwise
        """
        # Pattern for structured format: TYPE_DIAMETER_HOLDER_PARAMETERS_MATERIAL
        pattern = r'([A-Z]{3})_(\d+\.?\d*)_([^_]+)_?([^_]*?)_?([A-Z]*\d*)?'
        match = re.search(pattern, comment.upper())
        
        if match:
            tool_type = match.group(1)
            diameter_str = match.group(2)
            holder = match.group(3)
            parameters = match.group(4) if match.group(4) else ""
            material = match.group(5) if match.group(5) else ""
            
            # Set basic info
            tool_info.tool_type = tool_type
            tool_info.tool_type_name = self.tool_type_mapping.get(tool_type, tool_type)
            tool_info.diameter = float(diameter_str)
            tool_info.tool_holder = holder
            tool_info.material_code = material
            
            # Parse parameters (L19O25, etc.)
            if parameters:
                self._parse_parameters(parameters, tool_info)
            
            # Extract flute count from material code (AL3 = 3 flute)
            if material:
                flute_match = re.search(r'(\d+)$', material)
                if flute_match:
                    tool_info.flute_count = int(flute_match.group(1))
            
            return True
        
        return False
    
    def _parse_parameters(self, parameters: str, tool_info: ToolInfo):
        """Parse parameter string like L19O25"""
        # Flute length (L19)
        l_match = re.search(r'L(\d+\.?\d*)', parameters)
        if l_match:
            tool_info.flute_length = float(l_match.group(1))
        
        # Stickout (O25)
        o_match = re.search(r'O(\d+\.?\d*)', parameters)
        if o_match:
            tool_info.stickout = float(o_match.group(1))
        
        # Corner radius might be separate or in decimal format
        r_match = re.search(r'R(\d+\.?\d*)', parameters)
        if r_match:
            tool_info.corner_radius = float(r_match.group(1))
    
    def _extract_diameter_patterns(self, comment: str, tool_info: ToolInfo) -> bool:
        """
        Extract diameter using various patterns when structured format fails
        
        Common patterns:
        - D6.35, D06.35, Ø6.35
        - 6.35MM, 6.35mm
        - Numbers followed by common units
        
        Args:
            comment: Comment string to parse
            tool_info: ToolInfo object to populate
            
        Returns:
            True if diameter found, False otherwise
        """
        patterns = [
            r'[DØ](\d+\.?\d*)',  # D6.35, Ø6.35
            r'(\d+\.?\d*)\s*MM',  # 6.35MM, 6.35 MM
            r'(\d+\.?\d*)\s*mm',  # 6.35mm
            r'_(\d+\.?\d*)_',     # _6.35_
            r'(\d+\.?\d*)\s*DIA', # 6.35 DIA
            r'(\d{1,2}\.\d{1,2})', # Any decimal number 1-2 digits
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, comment.upper())
            if matches:
                try:
                    # Take the first reasonable diameter (0.1 to 50mm range)
                    for match in matches:
                        diameter = float(match)
                        if 0.1 <= diameter <= 50.0:
                            tool_info.diameter = diameter
                            
                            # Try to guess tool type from context
                            self._guess_tool_type(comment, tool_info)
                            return True
                except ValueError:
                    continue
        
        return False
    
    def _guess_tool_type(self, comment: str, tool_info: ToolInfo):
        """Guess tool type based on comment content"""
        comment_upper = comment.upper()
        
        if any(word in comment_upper for word in ['DRILL', 'DRL', 'BORE']):
            tool_info.tool_type = 'DRL'
            tool_info.tool_type_name = 'Drill'
        elif any(word in comment_upper for word in ['MILL', 'END', 'SEM']):
            tool_info.tool_type = 'SEM'
            tool_info.tool_type_name = 'Square End Mill'
        elif any(word in comment_upper for word in ['BALL', 'BAL']):
            tool_info.tool_type = 'BAL'
            tool_info.tool_type_name = 'Ball End Mill'
        elif any(word in comment_upper for word in ['CHAMFER', 'CHM']):
            tool_info.tool_type = 'CHM'
            tool_info.tool_type_name = 'Chamfer'
        elif any(word in comment_upper for word in ['TAP']):
            tool_info.tool_type = 'TAP'
            tool_info.tool_type_name = 'Tap'
        else:
            tool_info.tool_type = 'UNK'
            tool_info.tool_type_name = 'Unknown'
    
    def extract_all_tool_info(self, nc_file_path: str) -> Dict[str, ToolInfo]:
        """
        Parse entire NC file for tool comments
        
        Args:
            nc_file_path: Path to NC file
            
        Returns:
            Dictionary mapping tool_number -> ToolInfo
        """
        tool_info = {}
        current_tool = None
        
        try:
            with open(nc_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Check for tool calls to track current tool
                tool_call_match = re.search(r'TOOL CALL (\d+)', line)
                if tool_call_match:
                    current_tool = tool_call_match.group(1)
                    continue
                
                # Look for comments that might contain tool information
                if self._is_tool_comment(line):
                    # Try to find tool number in the comment
                    tool_num_match = re.search(r'T(\d+)', line)
                    if tool_num_match:
                        tool_number = tool_num_match.group(1)
                    elif current_tool:
                        tool_number = current_tool
                    else:
                        continue
                    
                    # Parse the comment
                    parsed_info = self.parse_tool_comment(line, tool_number)
                    if parsed_info:
                        tool_info[tool_number] = parsed_info
                        print(f"Parsed tool T{tool_number}: {parsed_info.tool_type_name}, Ø{parsed_info.diameter}mm")
        
        except Exception as e:
            print(f"Error reading NC file {nc_file_path}: {str(e)}")
        
        return tool_info
    
    def _is_tool_comment(self, line: str) -> bool:
        """
        Check if a line is likely to contain tool information
        
        Args:
            line: Line to check
            
        Returns:
            True if line might contain tool info
        """
        if not line:
            return False
        
        # Common comment indicators
        comment_indicators = [';', '(', '*', 'REM', '//']
        is_comment = any(line.startswith(indicator) for indicator in comment_indicators)
        
        if not is_comment:
            return False
        
        # Look for tool-related keywords or patterns
        tool_indicators = [
            'T\d+',  # T9
            '[DØ]\d',  # D6, Ø6
            '\d+\.?\d*MM',  # 6.35MM
            'MILL', 'DRILL', 'TAP', 'BALL', 'CHAMFER',
            'SEM', 'BAL', 'DRL', 'CHM', 'CHE'
        ]
        
        line_upper = line.upper()
        return any(re.search(pattern, line_upper) for pattern in tool_indicators)