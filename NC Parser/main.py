#!/usr/bin/env python3
"""
NC File G-code Parser and 3D Visualizer
Main application entry point
"""

import sys
import os
import argparse
from typing import Optional

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Now try to import the modules
try:
    from gcode_parser import GCodeParser
    from path_calculator import PathCalculator
    from point_cloud import PointCloudGenerator
    from visualizer import Visualizer
    print("✓ Core modules imported successfully")
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure the src directory exists and contains the required modules:")
    print("- src/gcode_parser.py")
    print("- src/path_calculator.py") 
    print("- src/point_cloud.py")
    print("- src/visualizer.py")
    print("\nAlso make sure core packages are installed:")
    print("pip install numpy matplotlib plotly pandas")
    sys.exit(1)

# Check for Open3D availability (optional)
OPEN3D_AVAILABLE = False
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
    print("✓ Open3D available - full functionality enabled")
except ImportError:
    print("⚠ Open3D not available - using alternative backends")
except Exception as e:
    print(f"⚠ Open3D import error: {e}")
    print("⚠ Using alternative backends without Open3D")

class NCParser:
    """Main application class for NC file processing and visualization."""
    
    def __init__(self):
        self.parser = GCodeParser()
        self.path_calculator = PathCalculator()
        self.point_cloud_generator = PointCloudGenerator()
        self.visualizer = None  # Initialize later with backend check
        
    def process_nc_file(self, file_path: str, 
                       tool_diameter: float = 6.0,
                       resolution: float = 0.1,
                       workpiece_resolution: float = 1.5,
                       visualization_backend: str = 'auto') -> dict:
        """
        Process NC file and generate visualizations.
        
        Args:
            file_path: Path to NC file
            tool_diameter: Cutting tool diameter in mm
            resolution: Path interpolation resolution in mm
            visualization_backend: Backend for visualization ('matplotlib', 'plotly', 'open3d', 'auto')
            
        Returns:
            Dictionary with processing results
        """
        try:
            print(f"Processing NC file: {file_path}")
            
            # Parse G-code
            print("Parsing G-code...")
            commands = self.parser.parse_file(file_path)
            
            if not commands:
                raise ValueError("No valid G-code commands found")
            
            # Get statistics
            stats = self.parser.get_statistics()
            print(f"Found {stats['total_commands']} total commands")
            print(f"Movement commands: {stats['movement_commands']}")
            
            # Calculate tool path
            print("Calculating tool path...")
            self.path_calculator.resolution = resolution
            path_points = self.path_calculator.calculate_tool_path(commands)
            
            if not path_points:
                raise ValueError("No tool path points generated")
            
            print(f"Generated {len(path_points)} tool path points")
            
            # Calculate material removal
            print("Calculating material removal...")
            removal_points = self.path_calculator.calculate_material_removal(
                path_points, tool_diameter
            )
            
            # Generate point clouds (without Open3D)
            print("Generating point clouds...")
            
            # Tool path point cloud (as numpy arrays)
            tool_path_points = path_points
            
            # Workpiece bounds
            bbox = stats['bounding_box']
            margin = tool_diameter
            workpiece_bounds = (
                (bbox['x'][0] - margin, bbox['x'][1] + margin),
                (bbox['y'][0] - margin, bbox['y'][1] + margin),
                (bbox['z'][0] - margin, bbox['z'][1] + margin)
            )
            
            # Create workpiece points
            workpiece_points = self.point_cloud_generator.create_workpiece_points(
                workpiece_bounds, resolution=workpiece_resolution
            )
            
            # Simulate material removal (simplified without Open3D)
            final_part_points = self.point_cloud_generator.simulate_removal_simple(
                workpiece_points, removal_points, tool_diameter / 2.0
            )
            
            # Calculate machining time
            machining_time = self.path_calculator.calculate_machining_time(commands)
            
            # Initialize visualizer with backend checking
            self.visualizer = Visualizer(backend=visualization_backend)
            
            # Results
            results = {
                'commands': commands,
                'path_points': path_points,
                'tool_path_points': tool_path_points,
                'workpiece_points': workpiece_points,
                'final_part_points': final_part_points,
                'statistics': stats,
                'machining_time_minutes': machining_time,
                'tool_diameter': tool_diameter,
                'resolution': resolution,
                'open3d_available': OPEN3D_AVAILABLE
            }
            
            print(f"Processing complete!")
            print(f"Estimated machining time: {machining_time:.2f} minutes")
            
            return results
            
        except Exception as e:
            print(f"Error processing NC file: {e}")
            raise
    
    def visualize_results(self, results: dict, show_analysis: bool = True, show_part_only: bool = False) -> None:
        """
        Create visualizations from processing results.
        
        Args:
            results: Results from process_nc_file
            show_analysis: Whether to show G-code analysis plots
        """
        try:
            print("Displaying visualizations...")
            
            # Show final machined part (most important visualization)
            if results['final_part_points']:
                print("Creating final machined part visualization...")
                workpiece_bounds = (
                    (results['statistics']['bounding_box']['x'][0] - results['tool_diameter'], 
                     results['statistics']['bounding_box']['x'][1] + results['tool_diameter']),
                    (results['statistics']['bounding_box']['y'][0] - results['tool_diameter'], 
                     results['statistics']['bounding_box']['y'][1] + results['tool_diameter']),
                    (results['statistics']['bounding_box']['z'][0] - results['tool_diameter'], 
                     results['statistics']['bounding_box']['z'][1] + results['tool_diameter'])
                )
                
                self.visualizer.plot_final_part(
                    results['final_part_points'], 
                    workpiece_bounds=workpiece_bounds,
                    title="Final Machined Part - What Remains After CNC Program"
                )
            
            # Tool path visualization (secondary) - skip if show_part_only is True
            if not show_part_only and results['tool_path_points']:
                print("Creating tool path visualization...")
                self.visualizer.plot_tool_path(
                    results['tool_path_points'], 
                    title="CNC Tool Path"
                )
            
            # G-code analysis (if plotly is available)
            if show_analysis and hasattr(self.visualizer, 'plot_gcode_analysis'):
                try:
                    self.visualizer.plot_gcode_analysis(results['commands'])
                except Exception as e:
                    print(f"Could not create analysis plots: {e}")
            
        except Exception as e:
            print(f"Error creating visualizations: {e}")
    
    def export_results(self, results: dict, output_dir: str = "output") -> None:
        """
        Export processing results to files.
        
        Args:
            results: Results from process_nc_file
            output_dir: Output directory
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Export point clouds as PLY files (without Open3D)
            tool_path_file = os.path.join(output_dir, "tool_path.ply")
            final_part_file = os.path.join(output_dir, "final_part.ply")
            
            # Export tool path points
            if results['tool_path_points']:
                self._export_points_as_ply(results['tool_path_points'], tool_path_file)
                print(f"Exported tool path points: {tool_path_file}")
            
            # Export final part points
            if results['final_part_points']:
                self._export_points_as_ply(results['final_part_points'], final_part_file)
                print(f"Exported final part points: {final_part_file}")
            
            # Export statistics
            stats_file = os.path.join(output_dir, "statistics.txt")
            with open(stats_file, 'w') as f:
                stats = results['statistics']
                f.write("NC File Processing Statistics\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"File format: {stats.get('file_format', 'Standard G-code')}\n")
                f.write(f"Total commands: {stats['total_commands']}\n")
                f.write(f"Movement commands: {stats['movement_commands']}\n")
                
                # Handle different file formats
                if stats.get('file_format') == 'Heidenhain':
                    f.write(f"Rapid moves (L_RAPID): {stats['rapid_moves']}\n")
                    f.write(f"Linear moves (L_FEED): {stats['linear_moves']}\n") 
                    f.write(f"Clockwise arcs (C_CW): {stats['clockwise_arcs']}\n")
                    f.write(f"Counter-clockwise arcs (C_CCW): {stats['counter_clockwise_arcs']}\n")
                    f.write(f"General arcs (C): {stats.get('general_arcs', 0)}\n")
                    
                    # Add tool information
                    if stats.get('tools'):
                        f.write(f"\nTools found:\n")
                        for tool_name, tool_info in stats['tools'].items():
                            f.write(f"  {tool_name}: {tool_info['cutter_type']}, D{tool_info['diameter']}mm\n")
                            f.write(f"    Corner radius: {tool_info['corner_radius']}mm\n")
                            f.write(f"    Material: {tool_info['material_type']}, {tool_info['num_flutes']} flutes\n")
                else:
                    f.write(f"Rapid moves (G00): {stats['rapid_moves']}\n")
                    f.write(f"Linear moves (G01): {stats['linear_moves']}\n")
                    f.write(f"Clockwise arcs (G02): {stats['clockwise_arcs']}\n")
                    f.write(f"Counter-clockwise arcs (G03): {stats['counter_clockwise_arcs']}\n")
                
                bbox = stats['bounding_box']
                f.write(f"Bounding box:\n")
                f.write(f"  X: {bbox['x'][0]:.2f} to {bbox['x'][1]:.2f} mm\n")
                f.write(f"  Y: {bbox['y'][0]:.2f} to {bbox['y'][1]:.2f} mm\n")
                f.write(f"  Z: {bbox['z'][0]:.2f} to {bbox['z'][1]:.2f} mm\n\n")
                
                f.write(f"Dimensions:\n")
                f.write(f"  X range: {stats['x_range']:.2f} mm\n")
                f.write(f"  Y range: {stats['y_range']:.2f} mm\n")
                f.write(f"  Z range: {stats['z_range']:.2f} mm\n\n")
                
                f.write(f"Processing parameters:\n")
                f.write(f"  Tool diameter: {results['tool_diameter']:.2f} mm\n")
                f.write(f"  Path resolution: {results['resolution']:.2f} mm\n")
                f.write(f"  Generated path points: {len(results['tool_path_points'])}\n")
                f.write(f"  Estimated machining time: {results['machining_time_minutes']:.2f} minutes\n")
                f.write(f"  Open3D available: {results['open3d_available']}\n")
            
            print(f"Exported statistics: {stats_file}")
            
        except Exception as e:
            print(f"Error exporting results: {e}")
    
    def _export_points_as_ply(self, points, filename):
        """Export points as PLY file without Open3D"""
        try:
            import numpy as np
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
                    
        except Exception as e:
            print(f"Error exporting PLY file: {e}")


def create_sample_nc_file():
    """Create a sample NC file for testing."""
    sample_content = """
; Sample NC file for testing
; Simple rectangular pocket
G90 ; Absolute positioning
G21 ; Metric units
G17 ; XY plane
M03 S1000 ; Spindle on clockwise

; Rapid to start position
G00 X0 Y0 Z5
G00 Z1

; Plunge to cutting depth
G01 Z-2 F100

; Rectangular pocket (20x10mm)
G01 X20 Y0 F200
G01 X20 Y10
G01 X0 Y10
G01 X0 Y0

; Inner rectangle
G01 X5 Y2.5
G01 X15 Y2.5
G01 X15 Y7.5
G01 X5 Y7.5
G01 X5 Y2.5

; Circular interpolation example
G02 X10 Y5 I5 J2.5

; Retract
G00 Z5

; Spindle off and end
M05
M30
"""
    
    os.makedirs("examples", exist_ok=True)
    with open("examples/sample.nc", 'w') as f:
        f.write(sample_content)
    
    print("Created sample NC file: examples/sample.nc")


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(description="NC File G-code Parser and 3D Visualizer with Multithreading")
    parser.add_argument("file", nargs='?', help="NC file to process")
    parser.add_argument("--tool-diameter", type=float, default=6.0, 
                       help="Tool diameter in mm (default: 6.0)")
    parser.add_argument("--resolution", type=float, default=0.1,
                       help="Path interpolation resolution in mm (default: 0.1)")
    parser.add_argument("--backend", choices=['matplotlib', 'plotly', 'auto'], 
                       default='auto', help="Visualization backend")
    parser.add_argument("--export", type=str, help="Export results to directory")
    parser.add_argument("--create-sample", action='store_true', 
                       help="Create sample NC file for testing")
    parser.add_argument("--no-viz", action='store_true', 
                       help="Skip visualizations")
    parser.add_argument("--threads", type=int, default=0,
                       help="Number of threads to use (0=auto detect, default: 0)")
    parser.add_argument("--fast", action='store_true',
                       help="Fast mode: lower resolution and fewer points for large files")
    parser.add_argument("--show-part-only", action='store_true',
                       help="Show only the final machined part (skip tool path visualization)")
    parser.add_argument("--workpiece-resolution", type=float, default=1.5,
                       help="Workpiece point resolution in mm for part visualization (default: 1.5)")
    
    args = parser.parse_args()
    
    # Apply fast mode settings
    if args.fast:
        if args.resolution < 1.0:
            args.resolution = max(1.0, args.resolution * 5)  # Increase resolution for speed
        print(f"Fast mode enabled: resolution={args.resolution}")
    
    # Create sample file if requested
    if args.create_sample:
        create_sample_nc_file()
        if not args.file:
            args.file = "examples/sample.nc"
    
    if not args.file:
        print("Error: No NC file specified. Use --create-sample to create a test file.")
        parser.print_help()
        return 1
    
    try:
        # Initialize application
        app = NCParser()
        
        # Configure threading if specified
        if args.threads > 0:
            app.path_calculator.num_threads = min(args.threads, 16)
            app.point_cloud_generator.num_threads = min(args.threads, 16)
            print(f"Using {args.threads} threads")
        
        # Process NC file
        results = app.process_nc_file(
            args.file,
            tool_diameter=args.tool_diameter,
            resolution=args.resolution,
            workpiece_resolution=args.workpiece_resolution,
            visualization_backend=args.backend
        )
        
        # Show visualizations
        if not args.no_viz:
            app.visualize_results(results, show_part_only=args.show_part_only)
        
        # Export results if requested
        if args.export:
            app.export_results(results, args.export)
        
        print("Processing completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
