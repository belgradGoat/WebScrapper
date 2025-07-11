import re
import numpy as np
from typing import List, Dict, Tuple, Optional, Union


class ToolInfo:
    """Represents tool information extracted from Heidenhain tool comments."""
    
    def __init__(self, tool_string: str, tool_number: int = None):
        self.raw_string = tool_string
        self.tool_number = tool_number
        self.cutter_type = ""
        self.diameter = 0.0
        self.holder_type = ""
        self.flute_length = 0.0
        self.stickout = 0.0
        self.corner_radius = 0.0
        self.material_type = ""
        self.num_flutes = 0
        
        self._parse_tool_string(tool_string)
    
    def _parse_tool_string(self, tool_string: str):
        """Parse Heidenhain tool string format: SEM_06.35_P15-120_L19O25_0.00AL3"""
        try:
            # Remove any leading/trailing whitespace and asterisks
            clean_string = tool_string.strip().strip('*').strip('-').strip()
            
            # Split by underscores
            parts = clean_string.split('_')
            
            if len(parts) >= 5:
                # Part 1: Cutter type (SEM, BAL, BUL, CHM, DRL, etc.)
                self.cutter_type = parts[0].upper()
                
                # Part 2: Diameter (06.35)
                try:
                    self.diameter = float(parts[1])
                except ValueError:
                    self.diameter = 0.0
                
                # Part 3: Holder type (P15-120) - not important for now
                self.holder_type = parts[2]
                
                # Part 4: Flute length and stickout (L19O25)
                flute_part = parts[3]
                if flute_part.startswith('L') and 'O' in flute_part:
                    l_pos = flute_part.find('L')
                    o_pos = flute_part.find('O')
                    if l_pos >= 0 and o_pos > l_pos:
                        try:
                            self.flute_length = float(flute_part[l_pos+1:o_pos])
                            self.stickout = float(flute_part[o_pos+1:])
                        except ValueError:
                            pass
                
                # Part 5: Corner radius + material + flutes (0.00AL3)
                last_part = parts[4]
                # Extract corner radius (number at start)
                radius_match = re.match(r'^([0-9]+\.?[0-9]*)', last_part)
                if radius_match:
                    try:
                        self.corner_radius = float(radius_match.group(1))
                    except ValueError:
                        pass
                
                # Extract material type and number of flutes
                material_match = re.search(r'([A-Z]+)([0-9]+)$', last_part)
                if material_match:
                    self.material_type = material_match.group(1)
                    try:
                        self.num_flutes = int(material_match.group(2))
                    except ValueError:
                        pass
                        
        except Exception as e:
            print(f"Warning: Could not parse tool string '{tool_string}': {e}")
    
    def get_cutter_type_description(self) -> str:
        """Get human-readable description of cutter type."""
        descriptions = {
            'SEM': 'Square End Mill',
            'BAL': 'Ball End Mill', 
            'BUL': 'Bull End Mill',
            'CHM': 'Chamfer Mill',
            'DRL': 'Drill',
            'BEM': 'Ball End Mill'  # Alternative naming
        }
        return descriptions.get(self.cutter_type, f'Unknown ({self.cutter_type})')
    
    def __repr__(self):
        return f"ToolInfo(T{self.tool_number}, {self.get_cutter_type_description()}, D{self.diameter}mm)"


class GCodeCommand:
    """Represents a single G-code or Heidenhain command with its parameters."""
    
    def __init__(self, command: str, x: float = None, y: float = None, z: float = None, 
                 i: float = None, j: float = None, k: float = None, f: float = None,
                 is_heidenhain: bool = False, radius: float = None, direction: str = None):
        self.command = command.upper()
        self.x = x
        self.y = y
        self.z = z
        self.i = i  # Arc center offset X (standard G-code) or absolute center X (Heidenhain)
        self.j = j  # Arc center offset Y (standard G-code) or absolute center Y (Heidenhain)
        self.k = k  # Arc center offset Z
        self.f = f  # Feed rate
        self.is_heidenhain = is_heidenhain
        self.radius = radius      # Arc radius (Heidenhain)
        self.direction = direction  # 'CW' or 'CCW' (Heidenhain)
        
    def __repr__(self):
        if self.is_heidenhain:
            return f"HCommand({self.command}, X={self.x}, Y={self.y}, Z={self.z})"
        return f"GCommand({self.command}, X={self.x}, Y={self.y}, Z={self.z})"


class GCodeParser:
    """Parser for G-code NC files and Heidenhain .H files."""
    
    def __init__(self):
        self.commands = []
        self.tools = {}  # Dictionary to store tool information
        self.current_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.current_feed_rate = 100.0
        self.current_spindle_speed = 0.0
        self.tool_number = 1
        self.is_heidenhain = False
        self.current_tool_info = None
        
        # Heidenhain-specific state
        self.arc_center = {'x': None, 'y': None}  # For circular moves
        self.stock_dimensions = {'length': 0, 'width': 0, 'height': 0}
        
    def parse_file(self, file_path: str) -> List[GCodeCommand]:
        """Parse a G-code file (.nc) or Heidenhain file (.h) and return a list of commands."""
        self.commands = []
        
        # Detect file type
        self.is_heidenhain = file_path.lower().endswith('.h')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    try:
                        if self.is_heidenhain:
                            # Parse Heidenhain format
                            command = self.parse_heidenhain_line(line.strip())
                        else:
                            # Parse standard G-code
                            command = self.parse_line(line.strip())
                            
                        if command:
                            self.commands.append(command)
                    except Exception as e:
                        print(f"Warning: Error parsing line {line_num}: {line.strip()} - {e}")
                        
        except FileNotFoundError:
            raise FileNotFoundError(f"NC file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file: {e}")
            
        return self.commands
    
    def parse_line(self, line: str) -> Optional[GCodeCommand]:
        """Parse a single line of G-code."""
        if not line or line.startswith(';') or line.startswith('('):
            return None  # Skip comments and empty lines
            
        # Remove comments
        line = re.sub(r';.*$', '', line)
        line = re.sub(r'\(.*?\)', '', line)
        line = line.strip().upper()
        
        if not line:
            return None
            
        # Extract G/M command
        g_match = re.search(r'[GM]\d+', line)
        if not g_match:
            return None
            
        command = g_match.group()
        
        # Extract coordinates and parameters
        x = self._extract_coordinate(line, 'X')
        y = self._extract_coordinate(line, 'Y')
        z = self._extract_coordinate(line, 'Z')
        i = self._extract_coordinate(line, 'I')
        j = self._extract_coordinate(line, 'J')
        k = self._extract_coordinate(line, 'K')
        f = self._extract_coordinate(line, 'F')
        
        # Update current position for incremental coordinates
        if x is not None:
            self.current_position['x'] = x
        if y is not None:
            self.current_position['y'] = y
        if z is not None:
            self.current_position['z'] = z
        if f is not None:
            self.current_feed_rate = f
            
        return GCodeCommand(command, x, y, z, i, j, k, f)
    
    def _extract_coordinate(self, line: str, axis: str) -> Optional[float]:
        """Extract coordinate value for given axis from G-code line."""
        pattern = f'{axis}([+-]?\\d*\\.?\\d+)'
        match = re.search(pattern, line)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def get_commands_by_type(self, command_type: str) -> List[GCodeCommand]:
        """Get all commands of a specific type (e.g., 'G01', 'G00')."""
        return [cmd for cmd in self.commands if cmd.command == command_type.upper()]
    
    def get_movement_commands(self) -> List[GCodeCommand]:
        """Get all movement commands (G00, G01, G02, G03 for standard G-code; L, C for Heidenhain)."""
        if self.is_heidenhain:
            movement_commands = ['L_RAPID', 'L_FEED', 'C', 'C_CW', 'C_CCW']
        else:
            movement_commands = ['G00', 'G01', 'G02', 'G03']
        return [cmd for cmd in self.commands if cmd.command in movement_commands]
    
    def get_bounding_box(self) -> Dict[str, Tuple[float, float]]:
        """Calculate the bounding box of all movements."""
        movement_commands = self.get_movement_commands()
        
        if not movement_commands:
            return {'x': (0, 0), 'y': (0, 0), 'z': (0, 0)}
        
        x_coords = [cmd.x for cmd in movement_commands if cmd.x is not None]
        y_coords = [cmd.y for cmd in movement_commands if cmd.y is not None]
        z_coords = [cmd.z for cmd in movement_commands if cmd.z is not None]
        
        return {
            'x': (min(x_coords) if x_coords else 0, max(x_coords) if x_coords else 0),
            'y': (min(y_coords) if y_coords else 0, max(y_coords) if y_coords else 0),
            'z': (min(z_coords) if z_coords else 0, max(z_coords) if z_coords else 0)
        }
    
    def get_statistics(self) -> Dict:
        """Get statistics about the parsed code."""
        movement_commands = self.get_movement_commands()
        bounding_box = self.get_bounding_box()
        
        stats = {
            'total_commands': len(self.commands),
            'movement_commands': len(movement_commands),
            'bounding_box': bounding_box,
            'x_range': bounding_box['x'][1] - bounding_box['x'][0],
            'y_range': bounding_box['y'][1] - bounding_box['y'][0],
            'z_range': bounding_box['z'][1] - bounding_box['z'][0],
            'file_format': 'Heidenhain' if self.is_heidenhain else 'Standard G-code',
            'tools': {}
        }
        
        if self.is_heidenhain:
            # Heidenhain-specific statistics
            stats.update({
                'rapid_moves': len(self.get_commands_by_type('L_RAPID')),
                'linear_moves': len(self.get_commands_by_type('L_FEED')),
                'clockwise_arcs': len(self.get_commands_by_type('C_CW')),
                'counter_clockwise_arcs': len(self.get_commands_by_type('C_CCW')),
                'general_arcs': len(self.get_commands_by_type('C')),
                'stock_dimensions': self.stock_dimensions
            })
            
            # Add tool information
            for tool_num, tool_info in self.tools.items():
                stats['tools'][f'T{tool_num}'] = {
                    'cutter_type': tool_info.get_cutter_type_description(),
                    'diameter': tool_info.diameter,
                    'corner_radius': tool_info.corner_radius,
                    'flute_length': tool_info.flute_length,
                    'stickout': tool_info.stickout,
                    'material_type': tool_info.material_type,
                    'num_flutes': tool_info.num_flutes,
                    'raw_string': tool_info.raw_string
                }
        else:
            # Standard G-code statistics
            stats.update({
                'rapid_moves': len(self.get_commands_by_type('G00')),
                'linear_moves': len(self.get_commands_by_type('G01')),
                'clockwise_arcs': len(self.get_commands_by_type('G02')),
                'counter_clockwise_arcs': len(self.get_commands_by_type('G03'))
            })
            
        return stats
    
    def parse_heidenhain_line(self, line: str) -> Optional[GCodeCommand]:
        """Parse a single line of Heidenhain code."""
        if not line:
            return None
            
        # Handle tool information comments
        if line.startswith('* -') and '_' in line and 'T' in line:
            tool_match = re.search(r'\* -(.+)\s+T(\d+)', line)
            if tool_match:
                tool_string = tool_match.group(1).strip()
                tool_num = int(tool_match.group(2))
                self.tools[tool_num] = ToolInfo(tool_string, tool_num)
                self.current_tool_info = self.tools[tool_num]
                print(f"Found tool T{tool_num}: {self.current_tool_info}")
            return None
            
        # Skip comments and empty lines
        if line.startswith(';') or line.startswith('*') or line.startswith('('):
            return None
            
        # Handle stock dimensions
        if line.startswith('; STOCK'):
            self._parse_stock_dimensions(line)
            return None
            
        # Remove comments
        line = re.sub(r';.*$', '', line)
        line = line.strip().upper()
        
        if not line:
            return None
            
        # Handle tool calls: TOOL CALL 7 Z S10000
        if line.startswith('TOOL CALL'):
            tool_match = re.search(r'TOOL CALL (\d+)', line)
            if tool_match:
                self.tool_number = int(tool_match.group(1))
                if self.tool_number in self.tools:
                    self.current_tool_info = self.tools[self.tool_number]
                    
                # Extract spindle speed if present
                speed_match = re.search(r'S(\d+)', line)
                if speed_match:
                    self.current_spindle_speed = float(speed_match.group(1))
            return None
            
        # Handle linear movements: L X+15.9092 Y+70.2758 FMAX
        if line.startswith('L '):
            x = self._extract_coordinate(line, 'X')
            y = self._extract_coordinate(line, 'Y')
            z = self._extract_coordinate(line, 'Z')
            f = None if 'FMAX' in line else self._extract_coordinate(line, 'F')
            
            command = 'L_RAPID' if 'FMAX' in line else 'L_FEED'
            
            if x is not None:
                self.current_position['x'] = x
            if y is not None:
                self.current_position['y'] = y
            if z is not None:
                self.current_position['z'] = z
            if f is not None:
                self.current_feed_rate = f
                
            return GCodeCommand(command, x, y, z, f=f, is_heidenhain=True)
            
        # Handle circular movements
        if line.startswith('CC '):
            # Store circle center
            x = self._extract_coordinate(line, 'X')
            y = self._extract_coordinate(line, 'Y')
            if x is not None:
                self.arc_center['x'] = x
            if y is not None:
                self.arc_center['y'] = y
            return None
            
        if line.startswith('C '):
            x = self._extract_coordinate(line, 'X')
            y = self._extract_coordinate(line, 'Y')
            z = self._extract_coordinate(line, 'Z')
            f = None if 'FMAX' in line else self._extract_coordinate(line, 'F')
            
            # Determine direction
            direction = 'CCW' if 'DR-' in line else 'CW' if 'DR+' in line else None
            command = 'C_CCW' if direction == 'CCW' else 'C_CW' if direction == 'CW' else 'C'
            
            # Calculate radius if center is known
            radius = None
            if self.arc_center['x'] is not None and self.arc_center['y'] is not None and x is not None and y is not None:
                dx = x - self.arc_center['x']
                dy = y - self.arc_center['y']
                radius = np.sqrt(dx*dx + dy*dy)
            
            if x is not None:
                self.current_position['x'] = x
            if y is not None:
                self.current_position['y'] = y
            if z is not None:
                self.current_position['z'] = z
            if f is not None:
                self.current_feed_rate = f
                
            return GCodeCommand(command, x, y, z, 
                              i=self.arc_center['x'], j=self.arc_center['y'],
                              f=f, is_heidenhain=True, radius=radius, direction=direction)
        
        return None
    
    def _parse_stock_dimensions(self, line: str):
        """Parse stock dimensions from Heidenhain comment."""
        if 'LENGTH' in line:
            match = re.search(r'LENGTH\s*=\s*([+-]?\d*\.?\d+)', line)
            if match:
                self.stock_dimensions['length'] = float(match.group(1))
        elif 'WIDTH' in line:
            match = re.search(r'WIDTH\s*=\s*([+-]?\d*\.?\d+)', line)
            if match:
                self.stock_dimensions['width'] = float(match.group(1))
        elif 'HEIGHT' in line:
            match = re.search(r'HEIGHT\s*=\s*([+-]?\d*\.?\d+)', line)
            if match:
                self.stock_dimensions['height'] = float(match.group(1))
    
    def _extract_coordinate(self, line: str, axis: str) -> Optional[float]:
        """Extract coordinate value for given axis from G-code or Heidenhain line."""
        # Handle both standard G-code format (X1.0) and Heidenhain format (X+1.0)
        pattern = f'{axis}([+-]?\\d*\\.?\\d+)'
        match = re.search(pattern, line)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def get_tools(self) -> Dict[int, ToolInfo]:
        """Get dictionary of all tools found in the file."""
        return self.tools
    
    def get_current_tool(self) -> Optional[ToolInfo]:
        """Get the currently active tool."""
        return self.current_tool_info
