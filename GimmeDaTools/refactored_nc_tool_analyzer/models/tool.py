"""
Tool model for NC Tool Analyzer
"""
from typing import Dict, Any, Optional


class Tool:
    """
    Represents a CNC tool with its properties and life data
    """
    def __init__(
        self,
        tool_number: str,
        current_time: float = 0.0,
        max_time: Optional[float] = None,
        status: str = "available"
    ):
        """
        Initialize a tool with its properties
        
        Args:
            tool_number: Tool identifier number
            current_time: Current usage time in minutes
            max_time: Maximum allowed usage time in minutes
            status: Tool status (available, locked, broken)
        """
        self.tool_number = tool_number
        self.current_time = current_time
        self.max_time = max_time
        self.status = status
        
    @property
    def usage_percentage(self) -> Optional[float]:
        """
        Calculate the usage percentage of the tool
        
        Returns:
            Percentage of tool life used or None if max_time is not set
        """
        if self.max_time is not None and self.max_time > 0:
            return (self.current_time / self.max_time) * 100
        return None
    
    @property
    def is_available(self) -> bool:
        """
        Check if the tool is available for use
        
        Returns:
            True if the tool is available, False otherwise
        """
        return self.status == "available"
    
    @property
    def is_critical(self) -> bool:
        """
        Check if the tool is in critical condition (near end of life)
        
        Returns:
            True if the tool usage is over 90%, False otherwise
        """
        percentage = self.usage_percentage
        return percentage is not None and percentage >= 90
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool to a dictionary for serialization
        
        Returns:
            Dictionary representation of the tool
        """
        return {
            'tool_number': self.tool_number,
            'current_time': self.current_time,
            'max_time': self.max_time,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tool':
        """
        Create a tool from a dictionary
        
        Args:
            data: Dictionary representation of a tool
            
        Returns:
            Tool instance
        """
        return cls(
            tool_number=data.get('tool_number', ''),
            current_time=data.get('current_time', 0.0),
            max_time=data.get('max_time'),
            status=data.get('status', 'available')
        )
    
    @classmethod
    def from_tool_life_data(cls, tool_number: str, tool_life_data: Dict[str, Any]) -> 'Tool':
        """
        Create a tool from tool life data format used in the original application
        
        Args:
            tool_number: Tool identifier number
            tool_life_data: Dictionary with tool life information
            
        Returns:
            Tool instance
        """
        current_time = tool_life_data.get('current_time', 0.0)
        max_time = tool_life_data.get('max_time')
        
        return cls(
            tool_number=tool_number,
            current_time=current_time,
            max_time=max_time,
            status="available"
        )