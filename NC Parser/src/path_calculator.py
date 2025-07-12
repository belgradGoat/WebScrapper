import numpy as np
import math
from typing import List, Tuple, Optional
from gcode_parser import GCodeCommand
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import partial
import time


class PathCalculator:
    """Calculates tool paths and generates interpolated points with multithreading support."""
    
    def __init__(self, resolution: float = 0.1):
        """
        Initialize path calculator.
        
        Args:
            resolution: Distance between interpolated points (mm)
        """
        self.resolution = resolution
        self.current_position = np.array([0.0, 0.0, 0.0])
        self.num_threads = min(mp.cpu_count(), 8)  # Limit to 8 threads max
        self.parallel_threshold = 1000  # Use parallel processing for files with >1000 commands
        print(f"PathCalculator initialized with {self.num_threads} threads")
        
    def calculate_tool_path(self, commands: List[GCodeCommand]) -> List[np.ndarray]:
        """
        Calculate complete tool path from G-code commands with parallel processing.
        
        Args:
            commands: List of G-code commands
            
        Returns:
            List of 3D points representing the tool path
        """
        start_time = time.time()
        print(f"Calculating tool path for {len(commands)} commands...")
        
        if len(commands) > self.parallel_threshold:
            print(f"Using parallel processing with {self.num_threads} threads")
            path_points = self._calculate_path_parallel(commands)
        else:
            print("Using single-threaded processing")
            path_points = self._calculate_path_sequential(commands)
        
        elapsed = time.time() - start_time
        print(f"Path calculation completed in {elapsed:.2f}s, generated {len(path_points)} points")
        return path_points
    
    def _calculate_path_sequential(self, commands: List[GCodeCommand]) -> List[np.ndarray]:
        """Calculate path using single thread (original method)."""
        path_points = []
        self.current_position = np.array([0.0, 0.0, 0.0])
        
        for command in commands:
            points = self._process_command(command)
            path_points.extend(points)
            
        return path_points
    
    def _calculate_path_parallel(self, commands: List[GCodeCommand]) -> List[np.ndarray]:
        """Calculate path using multiple threads for better performance."""
        try:
            # Split commands into chunks for parallel processing
            chunk_size = max(100, len(commands) // self.num_threads)
            command_chunks = [commands[i:i + chunk_size] for i in range(0, len(commands), chunk_size)]
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                chunk_results = list(executor.map(self._process_command_chunk, command_chunks))
            
            # Combine results
            all_points = []
            for chunk_points in chunk_results:
                all_points.extend(chunk_points)
                
            return all_points
            
        except Exception as e:
            print(f"Parallel processing failed: {e}, falling back to sequential")
            return self._calculate_path_sequential(commands)
    
    def _process_command_chunk(self, commands: List[GCodeCommand]) -> List[np.ndarray]:
        """Process a chunk of commands in a separate thread."""
        path_points = []
        current_pos = np.array([0.0, 0.0, 0.0])  # Local position tracker
        
        for command in commands:
            points = self._process_command_isolated(command, current_pos)
            path_points.extend(points)
            
            # Update local position
            if points:
                current_pos = points[-1].copy()
        
        return path_points
    
    def _process_command(self, command: GCodeCommand) -> List[np.ndarray]:
        """Process a single G-code command and return interpolated points."""
        points = []
        
        # Handle standard G-code commands
        if command.command in ['G00', 'G01']:
            # Linear movement
            points = self._interpolate_linear(command)
        elif command.command == 'G02':
            # Clockwise arc
            points = self._interpolate_arc(command, clockwise=True)
        elif command.command == 'G03':
            # Counter-clockwise arc
            points = self._interpolate_arc(command, clockwise=False)
        
        # Handle Heidenhain commands
        elif command.command in ['L_RAPID', 'L_FEED']:
            # Heidenhain linear movement
            points = self._interpolate_linear(command)
        elif command.command in ['C_CW', 'C_CCW', 'C']:
            # Heidenhain circular movement
            clockwise = command.command == 'C_CW'
            points = self._interpolate_heidenhain_arc(command, clockwise)
        
        return points
    
    def _process_command_isolated(self, command: GCodeCommand, current_pos: np.ndarray) -> List[np.ndarray]:
        """Process a single command with isolated position tracking for parallel processing."""
        points = []
        
        # Handle standard G-code commands
        if command.command in ['G00', 'G01']:
            points = self._interpolate_linear_isolated(command, current_pos)
        elif command.command == 'G02':
            points = self._interpolate_arc_isolated(command, current_pos, clockwise=True)
        elif command.command == 'G03':
            points = self._interpolate_arc_isolated(command, current_pos, clockwise=False)
        
        # Handle Heidenhain commands
        elif command.command in ['L_RAPID', 'L_FEED']:
            points = self._interpolate_linear_isolated(command, current_pos)
        elif command.command in ['C_CW', 'C_CCW', 'C']:
            clockwise = command.command == 'C_CW'
            points = self._interpolate_heidenhain_arc_isolated(command, current_pos, clockwise)
        
        return points
    
    def _interpolate_linear(self, command: GCodeCommand) -> List[np.ndarray]:
        """Interpolate points along a linear path."""
        # Get target position
        target = self._get_target_position(command)
        
        # Calculate distance and direction
        direction = target - self.current_position
        distance = np.linalg.norm(direction)
        
        if distance < 1e-6:  # Very small movement
            return []
        
        # Calculate number of points based on resolution
        num_points = max(1, int(distance / self.resolution))
        
        # Generate interpolated points
        points = []
        for i in range(1, num_points + 1):
            t = i / num_points
            point = self.current_position + t * direction
            points.append(point.copy())
        
        # Update current position
        self.current_position = target
        
        return points
    
    def _interpolate_linear_isolated(self, command: GCodeCommand, current_pos: np.ndarray) -> List[np.ndarray]:
        """Interpolate points along a linear path with isolated position tracking."""
        # Get target position
        target = self._get_target_position(command)
        
        # Calculate distance and direction
        direction = target - current_pos
        distance = np.linalg.norm(direction)
        
        if distance < 1e-6:  # Very small movement
            return []
        
        # Calculate number of points based on resolution
        num_points = max(1, int(distance / self.resolution))
        
        # Generate interpolated points
        points = []
        for i in range(1, num_points + 1):
            t = i / num_points
            point = current_pos + t * direction
            points.append(point.copy())
        
        return points
    
    def _interpolate_arc(self, command: GCodeCommand, clockwise: bool = True) -> List[np.ndarray]:
        """Interpolate points along an arc."""
        target = self._get_target_position(command)
        
        # Get arc center offsets
        i = command.i if command.i is not None else 0.0
        j = command.j if command.j is not None else 0.0
        
        # Calculate arc center
        center = self.current_position[:2] + np.array([i, j])
        
        # Calculate start and end angles
        start_vector = self.current_position[:2] - center
        end_vector = target[:2] - center
        
        start_angle = math.atan2(start_vector[1], start_vector[0])
        end_angle = math.atan2(end_vector[1], end_vector[0])
        
        # Calculate radius
        radius = np.linalg.norm(start_vector)
        
        # Adjust angles for clockwise/counter-clockwise
        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi
        
        # Calculate arc length and number of points
        angle_diff = abs(end_angle - start_angle)
        arc_length = radius * angle_diff
        num_points = max(1, int(arc_length / self.resolution))
        
        # Generate interpolated points
        points = []
        for i in range(1, num_points + 1):
            t = i / num_points
            angle = start_angle + t * (end_angle - start_angle)
            
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            
            # Linear interpolation for Z coordinate
            z = self.current_position[2] + t * (target[2] - self.current_position[2])
            
            points.append(np.array([x, y, z]))
        
        # Update current position
        self.current_position = target
        
        return points
    
    def _interpolate_arc_isolated(self, command: GCodeCommand, current_pos: np.ndarray, clockwise: bool = True) -> List[np.ndarray]:
        """Interpolate points along an arc with isolated position tracking."""
        target = self._get_target_position(command)
        
        # Get arc center offsets
        i = command.i if command.i is not None else 0.0
        j = command.j if command.j is not None else 0.0
        
        # Calculate arc center
        center = current_pos[:2] + np.array([i, j])
        
        # Calculate start and end angles
        start_vector = current_pos[:2] - center
        end_vector = target[:2] - center
        
        start_angle = math.atan2(start_vector[1], start_vector[0])
        end_angle = math.atan2(end_vector[1], end_vector[0])
        
        # Calculate radius
        radius = np.linalg.norm(start_vector)
        
        # Adjust angles for clockwise/counter-clockwise
        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi
        
        # Calculate arc length and number of points
        angle_diff = abs(end_angle - start_angle)
        arc_length = radius * angle_diff
        num_points = max(1, int(arc_length / self.resolution))
        
        # Generate interpolated points
        points = []
        for i in range(1, num_points + 1):
            t = i / num_points
            angle = start_angle + t * (end_angle - start_angle)
            
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            
            # Linear interpolation for Z coordinate
            z = current_pos[2] + t * (target[2] - current_pos[2])
            
            points.append(np.array([x, y, z]))
        
        return points
    
    def _interpolate_heidenhain_arc(self, command: GCodeCommand, clockwise: bool = True) -> List[np.ndarray]:
        """Interpolate points along a Heidenhain circular arc."""
        target = self._get_target_position(command)
        
        # For Heidenhain arcs, we need the center point
        if command.center_x is not None and command.center_y is not None:
            center = np.array([command.center_x, command.center_y, self.current_position[2]])
            
            # Calculate start and end angles
            start_vector = self.current_position[:2] - center[:2]
            end_vector = target[:2] - center[:2]
            
            start_angle = math.atan2(start_vector[1], start_vector[0])
            end_angle = math.atan2(end_vector[1], end_vector[0])
            
            # Calculate radius
            radius = np.linalg.norm(start_vector)
            
            # Determine arc sweep
            if clockwise:
                if end_angle > start_angle:
                    end_angle -= 2 * math.pi
                angle_sweep = start_angle - end_angle
            else:
                if end_angle < start_angle:
                    end_angle += 2 * math.pi
                angle_sweep = end_angle - start_angle
            
            # Calculate number of segments based on arc length
            arc_length = abs(angle_sweep * radius)
            num_segments = max(2, int(arc_length / self.resolution))
            
            points = []
            for i in range(num_segments + 1):
                t = i / num_segments
                if clockwise:
                    current_angle = start_angle - t * angle_sweep
                else:
                    current_angle = start_angle + t * angle_sweep
                
                x = center[0] + radius * math.cos(current_angle)
                y = center[1] + radius * math.sin(current_angle)
                
                # Interpolate Z linearly
                z = self.current_position[2] + t * (target[2] - self.current_position[2])
                
                points.append(np.array([x, y, z]))
            
            # Update position
            self.current_position = target
            return points
        else:
            # Fallback to linear interpolation if no arc center
            print("Warning: Arc center not defined, using linear interpolation")
            return self._interpolate_linear(command)
    
    def _interpolate_heidenhain_arc_isolated(self, command: GCodeCommand, current_pos: np.ndarray, clockwise: bool = True) -> List[np.ndarray]:
        """Interpolate points along a Heidenhain arc with isolated position tracking."""
        target = self._get_target_position(command)
        
        # Get center coordinates
        center_x = command.cc_x if command.cc_x is not None else current_pos[0]
        center_y = command.cc_y if command.cc_y is not None else current_pos[1]
        center = np.array([center_x, center_y])
        
        # Calculate start and end vectors
        start_vector = current_pos[:2] - center
        end_vector = target[:2] - center
        
        start_angle = math.atan2(start_vector[1], start_vector[0])
        end_angle = math.atan2(end_vector[1], end_vector[0])
        
        # Calculate radius
        radius = np.linalg.norm(start_vector)
        
        # Adjust angles for direction
        if clockwise:
            if end_angle > start_angle:
                end_angle -= 2 * math.pi
        else:
            if end_angle < start_angle:
                end_angle += 2 * math.pi
        
        # Calculate arc length and interpolation points
        angle_diff = abs(end_angle - start_angle)
        arc_length = radius * angle_diff
        num_points = max(1, int(arc_length / self.resolution))
        
        points = []
        for i in range(1, num_points + 1):
            t = i / num_points
            angle = start_angle + t * (end_angle - start_angle)
            
            x = center[0] + radius * math.cos(angle)
            y = center[1] + radius * math.sin(angle)
            z = current_pos[2] + t * (target[2] - current_pos[2])
            
            points.append(np.array([x, y, z]))
        
        return points
    
    def _get_target_position(self, command: GCodeCommand) -> np.ndarray:
        """Get target position from command, using current position for missing coordinates."""
        target = self.current_position.copy()
        
        if command.x is not None:
            target[0] = command.x
        if command.y is not None:
            target[1] = command.y
        if command.z is not None:
            target[2] = command.z
            
        return target
    
    def calculate_material_removal(self, path_points: List[np.ndarray], 
                                  tool_diameter: float = 6.0,
                                  workpiece_bounds: Optional[Tuple[Tuple[float, float], 
                                                                 Tuple[float, float], 
                                                                 Tuple[float, float]]] = None) -> List[np.ndarray]:
        """
        Calculate material removal simulation points.
        
        Args:
            path_points: Tool path points
            tool_diameter: Diameter of the cutting tool (mm)
            workpiece_bounds: ((x_min, x_max), (y_min, y_max), (z_min, z_max))
            
        Returns:
            List of points representing removed material
        """
        if not path_points:
            return []
        
        # Default workpiece bounds if not provided
        if workpiece_bounds is None:
            path_array = np.array(path_points)
            margin = tool_diameter
            workpiece_bounds = (
                (path_array[:, 0].min() - margin, path_array[:, 0].max() + margin),
                (path_array[:, 1].min() - margin, path_array[:, 1].max() + margin),
                (path_array[:, 2].min() - margin, path_array[:, 2].max() + margin)
            )
        
        tool_radius = tool_diameter / 2.0
        removal_points = []
        
        # Generate points around each tool position
        for point in path_points:
            # Create circular pattern around tool center
            angles = np.linspace(0, 2 * np.pi, 12, endpoint=False)
            
            for angle in angles:
                for radius in np.linspace(0, tool_radius, 3):
                    x = point[0] + radius * np.cos(angle)
                    y = point[1] + radius * np.sin(angle)
                    z = point[2]
                    
                    # Check if point is within workpiece bounds
                    if (workpiece_bounds[0][0] <= x <= workpiece_bounds[0][1] and
                        workpiece_bounds[1][0] <= y <= workpiece_bounds[1][1] and
                        workpiece_bounds[2][0] <= z <= workpiece_bounds[2][1]):
                        removal_points.append(np.array([x, y, z]))
        
        return removal_points
    
    def calculate_machining_time(self, commands: List[GCodeCommand]) -> float:
        """
        Estimate total machining time in minutes.
        
        Args:
            commands: List of G-code commands
            
        Returns:
            Estimated machining time in minutes
        """
        total_time = 0.0  # in minutes
        current_position = np.array([0.0, 0.0, 0.0])
        current_feed_rate = 100.0  # mm/min
        
        for command in commands:
            if command.f is not None:
                current_feed_rate = command.f
            
            target = current_position.copy()
            if command.x is not None:
                target[0] = command.x
            if command.y is not None:
                target[1] = command.y
            if command.z is not None:
                target[2] = command.z
            
            distance = np.linalg.norm(target - current_position)
            
            if command.command in ['G00', 'L_RAPID']:
                # Rapid movement - assume high speed
                time = distance / 3000.0  # Assume 3000 mm/min rapid
            elif command.command in ['G01', 'G02', 'G03', 'L_FEED', 'C_CW', 'C_CCW', 'C']:
                # Cutting movement
                time = distance / current_feed_rate if current_feed_rate > 0 else 0
            else:
                time = 0
            
            total_time += time
            current_position = target
        
        return total_time
