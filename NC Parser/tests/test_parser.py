import unittest
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.gcode_parser import GCodeParser, GCodeCommand


class TestGCodeParser(unittest.TestCase):
    """Test cases for G-code parser."""
    
    def setUp(self):
        self.parser = GCodeParser()
    
    def test_parse_basic_command(self):
        """Test parsing basic G-code command."""
        command = self.parser.parse_line("G01 X10 Y20 Z5 F100")
        
        self.assertIsNotNone(command)
        self.assertEqual(command.command, "G01")
        self.assertEqual(command.x, 10.0)
        self.assertEqual(command.y, 20.0)
        self.assertEqual(command.z, 5.0)
        self.assertEqual(command.f, 100.0)
    
    def test_parse_arc_command(self):
        """Test parsing arc command with I, J parameters."""
        command = self.parser.parse_line("G02 X10 Y10 I5 J0")
        
        self.assertIsNotNone(command)
        self.assertEqual(command.command, "G02")
        self.assertEqual(command.x, 10.0)
        self.assertEqual(command.y, 10.0)
        self.assertEqual(command.i, 5.0)
        self.assertEqual(command.j, 0.0)
    
    def test_ignore_comments(self):
        """Test that comments are ignored."""
        command = self.parser.parse_line("; This is a comment")
        self.assertIsNone(command)
        
        command = self.parser.parse_line("(Another comment)")
        self.assertIsNone(command)
    
    def test_parse_with_comments(self):
        """Test parsing command with inline comments."""
        command = self.parser.parse_line("G01 X10 Y20 ; Move to position")
        
        self.assertIsNotNone(command)
        self.assertEqual(command.command, "G01")
        self.assertEqual(command.x, 10.0)
        self.assertEqual(command.y, 20.0)
    
    def test_get_movement_commands(self):
        """Test filtering movement commands."""
        commands = [
            GCodeCommand("G00", 0, 0, 0),
            GCodeCommand("G01", 10, 0, 0),
            GCodeCommand("M03"),
            GCodeCommand("G02", 20, 10, 0, 10, 0),
        ]
        self.parser.commands = commands
        
        movement_commands = self.parser.get_movement_commands()
        self.assertEqual(len(movement_commands), 3)
        self.assertEqual(movement_commands[0].command, "G00")
        self.assertEqual(movement_commands[1].command, "G01")
        self.assertEqual(movement_commands[2].command, "G02")
    
    def test_bounding_box_calculation(self):
        """Test bounding box calculation."""
        commands = [
            GCodeCommand("G01", -5, -10, -2),
            GCodeCommand("G01", 15, 20, 8),
            GCodeCommand("G01", 0, 0, 0),
        ]
        self.parser.commands = commands
        
        bbox = self.parser.get_bounding_box()
        
        self.assertEqual(bbox['x'], (-5, 15))
        self.assertEqual(bbox['y'], (-10, 20))
        self.assertEqual(bbox['z'], (-2, 8))


if __name__ == '__main__':
    unittest.main()
