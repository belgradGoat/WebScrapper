"""
Machine model for NC Tool Analyzer
"""
from datetime import datetime
from typing import List, Dict, Optional, Any


class Machine:
    """
    Represents a CNC machine with its properties and tools
    """
    def __init__(
        self,
        machine_id: str,
        name: str,
        machine_type: str = "Machining Center",
        location: str = "",
        ip_address: str = "",
        tnc_folder: str = "",
        max_slots: int = 130,
        notes: str = ""
    ):
        """
        Initialize a machine with its properties
        
        Args:
            machine_id: Unique identifier for the machine
            name: Display name of the machine
            machine_type: Type of machine (e.g., "Machining Center")
            location: Physical location of the machine
            ip_address: IP address for network communication
            tnc_folder: TNC folder path for file transfers
            max_slots: Maximum number of tool slots
            notes: Additional notes about the machine
        """
        self.machine_id = machine_id
        self.name = name
        self.machine_type = machine_type
        self.location = location
        self.ip_address = ip_address
        self.tnc_folder = tnc_folder
        self.max_slots = max_slots
        self.notes = notes
        
        # Tool-related properties
        self.physical_tools: List[str] = []
        self.locked_tools: List[str] = []
        self.tool_life_data: Dict[str, Dict[str, Any]] = {}
        self.last_updated: Optional[str] = None
        
    def update_tools(
        self, 
        physical_tools: List[str], 
        locked_tools: List[str], 
        tool_life_data: Dict[str, Dict[str, Any]]
    ) -> None:
        """
        Update the machine's tool data
        
        Args:
            physical_tools: List of available tool numbers
            locked_tools: List of locked/broken tool numbers
            tool_life_data: Dictionary of tool life information
        """
        self.physical_tools = physical_tools
        self.locked_tools = locked_tools
        self.tool_life_data = tool_life_data
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the machine to a dictionary for serialization
        
        Returns:
            Dictionary representation of the machine
        """
        return {
            'id': self.machine_id,
            'name': self.name,
            'type': self.machine_type,
            'location': self.location,
            'ip_address': self.ip_address,
            'tnc_folder': self.tnc_folder,
            'max_slots': self.max_slots,
            'notes': self.notes,
            'physical_tools': self.physical_tools,
            'locked_tools': self.locked_tools,
            'tool_life_data': self.tool_life_data,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Machine':
        """
        Create a machine from a dictionary
        
        Args:
            data: Dictionary representation of a machine
            
        Returns:
            Machine instance
        """
        machine = cls(
            machine_id=data.get('id', ''),
            name=data.get('name', ''),
            machine_type=data.get('type', 'Machining Center'),
            location=data.get('location', ''),
            ip_address=data.get('ip_address', ''),
            tnc_folder=data.get('tnc_folder', ''),
            max_slots=data.get('max_slots', 130),
            notes=data.get('notes', '')
        )
        
        machine.physical_tools = data.get('physical_tools', [])
        machine.locked_tools = data.get('locked_tools', [])
        machine.tool_life_data = data.get('tool_life_data', {})
        machine.last_updated = data.get('last_updated')
        
        return machine