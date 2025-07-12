import numpy as np
from typing import List, Optional, Tuple, Any
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from functools import partial
import time


class PointCloudGenerator:
    """Generates and manipulates 3D point clouds from tool paths with multithreading support."""
    
    def __init__(self):
        self.num_threads = min(mp.cpu_count(), 6)  # Limit threads for memory usage
        self.parallel_threshold = 1000  # Use parallel processing for >1000 points
        print(f"PointCloudGenerator initialized with {self.num_threads} threads")
        
    def create_from_path(self, path_points: List[np.ndarray], 
                        color: Optional[Tuple[float, float, float]] = None) -> List[np.ndarray]:
        """Create point cloud from tool path points."""
        if not path_points:
            return []
        return path_points
    
    def create_workpiece_points(self, bounds: Tuple[Tuple[float, float], 
                                          Tuple[float, float], 
                                          Tuple[float, float]], 
                               resolution: float = 1.5) -> List[np.ndarray]:
        """Create workpiece points with adaptive resolution for better part definition."""
        try:
            x_min, x_max = bounds[0]
            y_min, y_max = bounds[1]
            z_min, z_max = bounds[2]
            
            print(f"Creating workpiece with {resolution}mm resolution...")
            print(f"Workpiece bounds: X({x_min:.1f} to {x_max:.1f}), Y({y_min:.1f} to {y_max:.1f}), Z({z_min:.1f} to {z_max:.1f})")
            
            # Create a grid of points
            x_points = np.arange(x_min, x_max + resolution, resolution)
            y_points = np.arange(y_min, y_max + resolution, resolution)
            z_points = np.arange(z_min, z_max + resolution, resolution)
            
            total_potential = len(x_points) * len(y_points) * len(z_points)
            print(f"Potential grid points: {total_potential}")
            
            points = []
            
            # Adaptive sampling based on total size
            if total_potential > 15000:
                print("Large workpiece detected, using optimized sampling...")
                # Sample more densely at boundaries, less in interior
                x_step = max(1, len(x_points) // 25)
                y_step = max(1, len(y_points) // 25) 
                z_step = max(1, len(z_points) // 15)
                
                for i, x in enumerate(x_points[::x_step]):
                    for j, y in enumerate(y_points[::y_step]):
                        for k, z in enumerate(z_points[::z_step]):
                            points.append(np.array([x, y, z]))
                            
                            # Add extra density near boundaries for better surface definition
                            if (i < 3 or i >= len(x_points[::x_step]) - 3 or
                                j < 3 or j >= len(y_points[::y_step]) - 3 or
                                k < 2 or k >= len(z_points[::z_step]) - 2):
                                # Add intermediate points near boundaries
                                if x + resolution/2 <= x_max:
                                    points.append(np.array([x + resolution/2, y, z]))
                                if y + resolution/2 <= y_max:
                                    points.append(np.array([x, y + resolution/2, z]))
            else:
                # Use full resolution for smaller workpieces
                for x in x_points:
                    for y in y_points:
                        for z in z_points:
                            points.append(np.array([x, y, z]))
            
            print(f"Created {len(points)} workpiece points")
            return points
            
        except Exception as e:
            print(f"Error creating workpiece points: {e}")
            return []
    
    def simulate_removal_simple(self, workpiece_points: List[np.ndarray], 
                               removal_points: List[np.ndarray], 
                               tool_radius: float) -> List[np.ndarray]:
        """Simulate material removal with enhanced accuracy for finished part visualization."""
        try:
            if not workpiece_points or not removal_points:
                return workpiece_points
            
            start_time = time.time()
            print(f"Starting enhanced material removal simulation...")
            print(f"Workpiece points: {len(workpiece_points)}")
            print(f"Tool path points: {len(removal_points)}")
            print(f"Tool radius: {tool_radius:.2f}mm")
            
            # Optimize datasets for better performance vs accuracy balance
            max_workpiece_points = 8000  # Increased for better part definition
            max_removal_points = 1000    # Increased for better accuracy
            
            # Sample workpiece points if too many, but keep boundary points
            if len(workpiece_points) > max_workpiece_points:
                wp_array = np.array(workpiece_points)
                
                # Always keep boundary points for better part definition
                x_min, x_max = wp_array[:, 0].min(), wp_array[:, 0].max()
                y_min, y_max = wp_array[:, 1].min(), wp_array[:, 1].max()
                z_min, z_max = wp_array[:, 2].min(), wp_array[:, 2].max()
                
                boundary_mask = (
                    (np.abs(wp_array[:, 0] - x_min) < 2.0) | (np.abs(wp_array[:, 0] - x_max) < 2.0) |
                    (np.abs(wp_array[:, 1] - y_min) < 2.0) | (np.abs(wp_array[:, 1] - y_max) < 2.0) |
                    (np.abs(wp_array[:, 2] - z_min) < 1.0) | (np.abs(wp_array[:, 2] - z_max) < 1.0)
                )
                
                boundary_points = wp_array[boundary_mask]
                interior_points = wp_array[~boundary_mask]
                
                # Sample interior points
                n_interior_to_keep = max(0, max_workpiece_points - len(boundary_points))
                if len(interior_points) > n_interior_to_keep:
                    indices = np.random.choice(len(interior_points), n_interior_to_keep, replace=False)
                    sampled_interior = interior_points[indices]
                else:
                    sampled_interior = interior_points
                
                # Combine boundary and sampled interior points
                sampled_workpiece = np.vstack([boundary_points, sampled_interior]) if len(sampled_interior) > 0 else boundary_points
                sampled_workpiece = [np.array(point) for point in sampled_workpiece]
                
                print(f"Sampled workpiece: {len(boundary_points)} boundary + {len(sampled_interior) if len(sampled_interior) > 0 else 0} interior = {len(sampled_workpiece)} total points")
            else:
                sampled_workpiece = workpiece_points
            
            # Sample removal points more intelligently
            if len(removal_points) > max_removal_points:
                # Keep points at regular intervals to maintain cutting accuracy
                step = len(removal_points) // max_removal_points
                sampled_removal = removal_points[::step]
                print(f"Sampled tool path to {len(sampled_removal)} points")
            else:
                sampled_removal = removal_points
            
            # Use parallel processing for large datasets
            if len(sampled_workpiece) > self.parallel_threshold:
                print(f"Using parallel processing with {self.num_threads} threads")
                remaining_points = self._simulate_removal_parallel(sampled_workpiece, sampled_removal, tool_radius)
            else:
                print("Using sequential processing")
                remaining_points = self._simulate_removal_sequential(sampled_workpiece, sampled_removal, tool_radius)
            
            elapsed = time.time() - start_time
            material_removed_pct = 100 * (len(sampled_workpiece) - len(remaining_points)) / len(sampled_workpiece)
            print(f"Material removal completed in {elapsed:.2f}s")
            print(f"Material removed: {len(sampled_workpiece) - len(remaining_points)} points ({material_removed_pct:.1f}%)")
            print(f"Final part: {len(remaining_points)} points remaining")
            
            return remaining_points
            
        except Exception as e:
            print(f"Error in material removal simulation: {e}")
            return workpiece_points[:1000]  # Return sample if error
    
    def create_detailed_workpiece_points(self, bounds: Tuple[Tuple[float, float], 
                                                    Tuple[float, float], 
                                                    Tuple[float, float]], 
                                        resolution: float = 1.0) -> List[np.ndarray]:
        """Create high-resolution workpiece points for better part visualization."""
        try:
            x_min, x_max = bounds[0]
            y_min, y_max = bounds[1]
            z_min, z_max = bounds[2]
            
            print(f"Creating detailed workpiece with {resolution}mm resolution...")
            
            # Create a denser grid for better part definition
            x_points = np.arange(x_min, x_max + resolution, resolution)
            y_points = np.arange(y_min, y_max + resolution, resolution)
            z_points = np.arange(z_min, z_max + resolution, resolution)
            
            points = []
            total_points = len(x_points) * len(y_points) * len(z_points)
            
            # Limit total points for performance
            if total_points > 50000:
                print(f"Large workpiece detected ({total_points} points), using adaptive sampling")
                # Use adaptive sampling - denser near edges, sparser in center
                x_step = max(1, len(x_points) // 30)
                y_step = max(1, len(y_points) // 30)
                z_step = max(1, len(z_points) // 20)
                
                for i, x in enumerate(x_points[::x_step]):
                    for j, y in enumerate(y_points[::y_step]):
                        for k, z in enumerate(z_points[::z_step]):
                            points.append(np.array([x, y, z]))
            else:
                for x in x_points:
                    for y in y_points:
                        for z in z_points:
                            points.append(np.array([x, y, z]))
            
            print(f"Created {len(points)} workpiece points")
            return points
            
        except Exception as e:
            print(f"Error creating detailed workpiece points: {e}")
            return []
    
    def simulate_advanced_removal(self, workpiece_points: List[np.ndarray], 
                                 tool_path_points: List[np.ndarray], 
                                 tool_radius: float,
                                 layer_by_layer: bool = True) -> List[np.ndarray]:
        """
        Advanced material removal simulation with layer-by-layer processing.
        
        Args:
            workpiece_points: Original workpiece points
            tool_path_points: Tool path points
            tool_radius: Tool radius
            layer_by_layer: Process removal layer by layer for better accuracy
        """
        try:
            if not workpiece_points or not tool_path_points:
                return workpiece_points
            
            start_time = time.time()
            print(f"Starting advanced material removal simulation...")
            print(f"Workpiece points: {len(workpiece_points)}")
            print(f"Tool path points: {len(tool_path_points)}")
            print(f"Tool radius: {tool_radius}mm")
            
            # Convert to numpy arrays for faster processing
            wp_array = np.array(workpiece_points)
            tool_array = np.array(tool_path_points)
            
            if layer_by_layer:
                remaining_points = self._simulate_removal_by_layers(wp_array, tool_array, tool_radius)
            else:
                remaining_points = self._simulate_removal_parallel(workpiece_points, tool_path_points, tool_radius)
            
            elapsed = time.time() - start_time
            print(f"Advanced material removal completed in {elapsed:.2f}s")
            print(f"Material removed: {len(workpiece_points) - len(remaining_points)} points")
            print(f"Material remaining: {len(remaining_points)} points ({100*len(remaining_points)/len(workpiece_points):.1f}%)")
            
            return remaining_points
            
        except Exception as e:
            print(f"Error in advanced material removal: {e}")
            return self.simulate_removal_simple(workpiece_points, tool_path_points, tool_radius * 2)
    
    def _simulate_removal_sequential(self, workpiece_points: List[np.ndarray], 
                                   removal_points: List[np.ndarray], 
                                   tool_radius: float) -> List[np.ndarray]:
        """Sequential material removal (original method)."""
        remaining_points = []
        
        for i, wp_point in enumerate(workpiece_points):
            if i % 500 == 0:
                print(f"Processing point {i}/{len(workpiece_points)}")
            
            is_removed = False
            for removal_point in removal_points:
                distance = np.linalg.norm(wp_point - np.array(removal_point))
                if distance <= tool_radius:
                    is_removed = True
                    break
            
            if not is_removed:
                remaining_points.append(wp_point)
        
        return remaining_points
    
    def _simulate_removal_parallel(self, workpiece_points: List[np.ndarray], 
                                 removal_points: List[np.ndarray], 
                                 tool_radius: float) -> List[np.ndarray]:
        """Parallel material removal for better performance."""
        try:
            # Split workpiece points into chunks
            chunk_size = max(50, len(workpiece_points) // self.num_threads)
            workpiece_chunks = [workpiece_points[i:i + chunk_size] for i in range(0, len(workpiece_points), chunk_size)]
            
            # Process chunks in parallel
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                process_func = partial(self._process_removal_chunk, removal_points=removal_points, tool_radius=tool_radius)
                chunk_results = list(executor.map(process_func, workpiece_chunks))
            
            # Combine results
            remaining_points = []
            for chunk_result in chunk_results:
                remaining_points.extend(chunk_result)
            
            return remaining_points
            
        except Exception as e:
            print(f"Parallel removal failed: {e}, falling back to sequential")
            return self._simulate_removal_sequential(workpiece_points, removal_points, tool_radius)
    
    @staticmethod
    def _process_removal_chunk(workpiece_chunk: List[np.ndarray], 
                             removal_points: List[np.ndarray], 
                             tool_radius: float) -> List[np.ndarray]:
        """Process a chunk of workpiece points for removal simulation."""
        remaining_points = []
        
        for wp_point in workpiece_chunk:
            is_removed = False
            for removal_point in removal_points:
                distance = np.linalg.norm(wp_point - np.array(removal_point))
                if distance <= tool_radius:
                    is_removed = True
                    break
            
            if not is_removed:
                remaining_points.append(wp_point)
        
        return remaining_points
    
    def export_ply(self, points: List[np.ndarray], filename: str) -> bool:
        """Export points as PLY file."""
        try:
            points_array = np.array(points)
            
            with open(filename, 'w') as f:
                f.write("ply\n")
                f.write("format ascii 1.0\n")
                f.write(f"element vertex {len(points_array)}\n")
                f.write("property float x\n")
                f.write("property float y\n")
                f.write("property float z\n")
                f.write("end_header\n")
                
                for point in points_array:
                    f.write(f"{point[0]:.6f} {point[1]:.6f} {point[2]:.6f}\n")
            
            return True
            
        except Exception as e:
            print(f"Error exporting PLY file: {e}")
            return False
    
    def _simulate_removal_by_layers(self, wp_array: np.ndarray, tool_array: np.ndarray, tool_radius: float) -> List[np.ndarray]:
        """Simulate removal layer by layer for more accurate results."""
        # Sort points by Z coordinate for layer processing
        z_levels = np.unique(wp_array[:, 2])
        z_levels = np.sort(z_levels)[::-1]  # Process from top to bottom
        
        remaining_points = []
        
        print(f"Processing {len(z_levels)} layers...")
        
        for i, z_level in enumerate(z_levels):
            if i % max(1, len(z_levels) // 10) == 0:
                print(f"Processing layer {i+1}/{len(z_levels)} (Z={z_level:.2f})")
            
            # Get workpiece points at this layer
            layer_mask = np.abs(wp_array[:, 2] - z_level) < 0.1  # Small tolerance
            layer_points = wp_array[layer_mask]
            
            if len(layer_points) == 0:
                continue
            
            # Get tool positions that affect this layer
            tool_mask = tool_array[:, 2] <= z_level + tool_radius
            relevant_tools = tool_array[tool_mask]
            
            # Check each workpiece point in this layer
            for wp_point in layer_points:
                is_removed = False
                
                # Check against relevant tool positions
                for tool_point in relevant_tools:
                    # Calculate 3D distance
                    distance = np.linalg.norm(wp_point - tool_point)
                    if distance <= tool_radius:
                        is_removed = True
                        break
                
                if not is_removed:
                    remaining_points.append(wp_point)
        
        return remaining_points
