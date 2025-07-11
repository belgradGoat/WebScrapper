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
                                          Tuple[float, float]]) -> List[np.ndarray]:
        """Create workpiece points."""
        try:
            x_min, x_max = bounds[0]
            y_min, y_max = bounds[1]
            z_min, z_max = bounds[2]
            
            # Create a grid of points
            resolution = 2.0  # 2mm spacing for performance
            
            x_points = np.arange(x_min, x_max + resolution, resolution)
            y_points = np.arange(y_min, y_max + resolution, resolution)
            z_points = np.arange(z_min, z_max + resolution, resolution)
            
            points = []
            for x in x_points:
                for y in y_points:
                    for z in z_points:
                        points.append(np.array([x, y, z]))
            
            return points
            
        except Exception as e:
            print(f"Error creating workpiece points: {e}")
            return []
    
    def simulate_removal_simple(self, workpiece_points: List[np.ndarray], 
                               removal_points: List[np.ndarray], 
                               tool_radius: float) -> List[np.ndarray]:
        """Simulate material removal with parallel processing."""
        try:
            if not workpiece_points or not removal_points:
                return workpiece_points
            
            start_time = time.time()
            print(f"Starting material removal simulation...")
            print(f"Workpiece points: {len(workpiece_points)}")
            print(f"Removal points: {len(removal_points)}")
            
            # Optimize datasets for performance
            max_workpiece_points = 5000
            max_removal_points = 500
            
            # Sample workpiece points if too many
            if len(workpiece_points) > max_workpiece_points:
                indices = np.random.choice(len(workpiece_points), max_workpiece_points, replace=False)
                sampled_workpiece = [workpiece_points[i] for i in indices]
                print(f"Sampled workpiece to {len(sampled_workpiece)} points")
            else:
                sampled_workpiece = workpiece_points
            
            # Sample removal points if too many
            if len(removal_points) > max_removal_points:
                step = len(removal_points) // max_removal_points
                sampled_removal = removal_points[::step]
                print(f"Sampled removal points to {len(sampled_removal)} points")
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
            print(f"Material removal completed in {elapsed:.2f}s: {len(remaining_points)} points remaining")
            return remaining_points
            
        except Exception as e:
            print(f"Error in material removal simulation: {e}")
            return workpiece_points[:1000]  # Return sample if error
    
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
