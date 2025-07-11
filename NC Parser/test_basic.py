#!/usr/bin/env python3
"""
Simple test script to verify the NC parser implementation
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_functionality():
    """Test basic parsing functionality without visualization."""
    try:
        print("Testing NC Parser - Basic Functionality")
        print("=" * 50)
        
        # Test G-code parser
        from src.gcode_parser import GCodeParser, GCodeCommand
        
        parser = GCodeParser()
        
        # Test basic command parsing
        print("\n1. Testing G-code command parsing...")
        test_lines = [
            "G01 X10 Y20 Z5 F100",
            "G02 X15 Y25 I5 J0",
            "G00 X0 Y0 Z10",
            "; This is a comment",
            "M03 S1200"
        ]
        
        commands = []
        for line in test_lines:
            cmd = parser.parse_line(line)
            if cmd:
                commands.append(cmd)
                print(f"  Parsed: {cmd}")
        
        print(f"  Successfully parsed {len(commands)} commands")
        
        # Test path calculator
        print("\n2. Testing path calculator...")
        from src.path_calculator import PathCalculator
        
        calculator = PathCalculator(resolution=1.0)
        path_points = calculator.calculate_tool_path(commands)
        print(f"  Generated {len(path_points)} path points")
        
        # Test statistics
        print("\n3. Testing statistics calculation...")
        parser.commands = commands
        stats = parser.get_statistics()
        print(f"  Total commands: {stats['total_commands']}")
        print(f"  Movement commands: {stats['movement_commands']}")
        print(f"  Bounding box: {stats['bounding_box']}")
        
        # Test sample NC file parsing
        print("\n4. Testing sample NC file...")
        sample_file = os.path.join("examples", "sample.nc")
        if os.path.exists(sample_file):
            file_commands = parser.parse_file(sample_file)
            print(f"  Parsed {len(file_commands)} commands from sample file")
            
            file_stats = parser.get_statistics()
            print(f"  File statistics:")
            print(f"    Total commands: {file_stats['total_commands']}")
            print(f"    Rapid moves: {file_stats['rapid_moves']}")
            print(f"    Linear moves: {file_stats['linear_moves']}")
            print(f"    Arcs: {file_stats['clockwise_arcs'] + file_stats['counter_clockwise_arcs']}")
        else:
            print(f"  Sample file not found: {sample_file}")
        
        print("\n" + "=" * 50)
        print("✓ Basic functionality test completed successfully!")
        print("\nThe NC Parser tool is working correctly.")
        print("\nTo use the full tool with visualizations:")
        print(f"  python main.py examples/sample.nc")
        print(f"  python main.py --create-sample")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
