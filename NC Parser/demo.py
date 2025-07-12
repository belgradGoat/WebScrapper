#!/usr/bin/env python3
"""
Demo script showing the NC Parser capabilities
"""

import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_demo_nc_file():
    """Create a simple demo NC file."""
    demo_content = """
; Demo NC file - Simple rectangular path
G90 ; Absolute positioning
G21 ; Metric units
M03 S1000 ; Spindle on

; Move to start position
G00 X0 Y0 Z5
G01 Z0 F50

; Rectangle 10x8mm
G01 X10 Y0 F100
G01 X10 Y8
G01 X0 Y8
G01 X0 Y0

; Retract
G00 Z5
M05 ; Spindle off
M30 ; End
"""
    
    os.makedirs("demo", exist_ok=True)
    with open("demo/rectangle.nc", 'w') as f:
        f.write(demo_content)
    
    return "demo/rectangle.nc"

def demo_nc_parser():
    """Demonstrate NC parser functionality."""
    try:
        print("NC File G-code Parser and 3D Visualizer - Demo")
        print("=" * 60)
        
        # Import modules
        from src.gcode_parser import GCodeParser
        from src.path_calculator import PathCalculator
        
        # Create demo file
        print("\n1. Creating demo NC file...")
        demo_file = create_demo_nc_file()
        print(f"   Created: {demo_file}")
        
        # Initialize parser
        print("\n2. Initializing parser...")
        parser = GCodeParser()
        calculator = PathCalculator(resolution=0.5)
        
        # Parse the file
        print("\n3. Parsing NC file...")
        commands = parser.parse_file(demo_file)
        print(f"   Parsed {len(commands)} commands")
        
        # Show some commands
        print("\n4. Sample commands:")
        for i, cmd in enumerate(commands[:8]):
            print(f"   {i+1:2d}: {cmd}")
        if len(commands) > 8:
            print(f"   ... and {len(commands)-8} more commands")
        
        # Calculate statistics
        print("\n5. File statistics:")
        stats = parser.get_statistics()
        print(f"   Total commands: {stats['total_commands']}")
        print(f"   Movement commands: {stats['movement_commands']}")
        print(f"   Rapid moves (G00): {stats['rapid_moves']}")
        print(f"   Linear moves (G01): {stats['linear_moves']}")
        
        bbox = stats['bounding_box']
        print(f"   Bounding box:")
        print(f"     X: {bbox['x'][0]:.1f} to {bbox['x'][1]:.1f} mm")
        print(f"     Y: {bbox['y'][0]:.1f} to {bbox['y'][1]:.1f} mm")
        print(f"     Z: {bbox['z'][0]:.1f} to {bbox['z'][1]:.1f} mm")
        
        # Calculate tool path
        print("\n6. Calculating tool path...")
        path_points = calculator.calculate_tool_path(commands)
        print(f"   Generated {len(path_points)} interpolated points")
        
        if path_points:
            # Show first and last few points
            print("   First 3 points:")
            for i, point in enumerate(path_points[:3]):
                print(f"     {i+1}: X={point[0]:6.2f}, Y={point[1]:6.2f}, Z={point[2]:6.2f}")
            
            print("   Last 3 points:")
            for i, point in enumerate(path_points[-3:], len(path_points)-2):
                print(f"     {i}: X={point[0]:6.2f}, Y={point[1]:6.2f}, Z={point[2]:6.2f}")
        
        # Calculate machining time
        print("\n7. Estimating machining time...")
        machining_time = calculator.calculate_machining_time(commands)
        print(f"   Estimated time: {machining_time:.2f} minutes")
        
        # Material removal simulation
        print("\n8. Material removal simulation...")
        tool_diameter = 3.0
        removal_points = calculator.calculate_material_removal(
            path_points, tool_diameter
        )
        print(f"   Tool diameter: {tool_diameter} mm")
        print(f"   Generated {len(removal_points)} material removal points")
        
        print("\n" + "=" * 60)
        print("✓ Demo completed successfully!")
        print("\nThe NC Parser can:")
        print("  • Parse G-code commands from NC files")
        print("  • Calculate interpolated tool paths")
        print("  • Simulate material removal")
        print("  • Generate statistics and analysis")
        print("  • Export point clouds and 3D models")
        print("\nFor full functionality with 3D visualization:")
        print("  python main.py demo/rectangle.nc")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demo_nc_parser()
    print(f"\nDemo {'successful' if success else 'failed'}!")
    sys.exit(0 if success else 1)
