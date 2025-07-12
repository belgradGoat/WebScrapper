import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.path_calculator import PathCalculator
from src.gcode_parser import GCodeCommand


class TestPathCalculator(unittest.TestCase):
    """Test cases for path calculator."""
    
    def setUp(self):
        self.calculator = PathCalculator(resolution=1.0)
    
    def test_linear_interpolation(self):
        """Test linear path interpolation."""
        command = GCodeCommand("G01", 10, 0, 0)
        self.calculator.current_position = np.array([0.0, 0.0, 0.0])
        
        points = self.calculator._interpolate_linear(command)
        
        self.assertGreater(len(points), 0)
        self.assertTrue(np.allclose(points[-1], [10, 0, 0]))
    
    def test_arc_interpolation(self):
        """Test arc interpolation."""
        # Quarter circle arc
        command = GCodeCommand("G02", 10, 10, 0, 10, 0)
        self.calculator.current_position = np.array([0.0, 0.0, 0.0])
        
        points = self.calculator._interpolate_arc(command, clockwise=True)
        
        self.assertGreater(len(points), 0)
        self.assertTrue(np.allclose(points[-1], [10, 10, 0], atol=1e-6))
    
    def test_tool_path_calculation(self):
        """Test complete tool path calculation."""
        commands = [
            GCodeCommand("G00", 0, 0, 5),  # Rapid to start
            GCodeCommand("G01", 0, 0, 0),  # Plunge
            GCodeCommand("G01", 10, 0, 0), # Linear move
            GCodeCommand("G01", 10, 10, 0), # Another linear move
        ]
        
        path_points = self.calculator.calculate_tool_path(commands)
        
        self.assertGreater(len(path_points), 0)
        # Should end at final position
        final_point = path_points[-1]
        self.assertTrue(np.allclose(final_point, [10, 10, 0]))
    
    def test_material_removal_calculation(self):
        """Test material removal point generation."""
        path_points = [
            np.array([0, 0, 0]),
            np.array([10, 0, 0]),
            np.array([10, 10, 0]),
        ]
        
        removal_points = self.calculator.calculate_material_removal(
            path_points, tool_diameter=2.0
        )
        
        self.assertGreater(len(removal_points), 0)
    
    def test_machining_time_calculation(self):
        """Test machining time estimation."""
        commands = [
            GCodeCommand("G00", 10, 0, 0),  # Rapid move
            GCodeCommand("G01", 20, 0, 0, f=100),  # Feed move
        ]
        
        time = self.calculator.calculate_machining_time(commands)
        
        self.assertGreater(time, 0)


if __name__ == '__main__':
    unittest.main()
