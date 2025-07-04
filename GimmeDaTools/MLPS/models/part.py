"""
Part model for Machine Shop Scheduler
"""
from typing import Dict, Any, Optional, Literal
import uuid


class Part:
    """
    Represents an individual part within a job
    """
    def __init__(
        self,
        part_id: Optional[str] = None,
        job_id: str = "",
        part_number: int = 1,
        machine_id: Optional[str] = None,
        start_time: int = 0,
        estimate: bool = True,
        status: Literal['scheduled', 'in-progress', 'completed'] = 'scheduled'
    ):
        """
        Initialize a part with its properties
        
        Args:
            part_id: Unique identifier for the part (generated if not provided)
            job_id: ID of the job this part belongs to
            part_number: Number of the part within the job
            machine_id: ID of the machine assigned to this part
            start_time: Start time as timestamp in milliseconds
            estimate: Whether the time is an estimate or confirmed
            status: Status of the part (scheduled, in-progress, completed)
        """
        self.part_id = part_id or f"part-{uuid.uuid4()}"
        self.job_id = job_id
        self.part_number = part_number
        self.machine_id = machine_id
        self.start_time = start_time
        self.estimate = estimate
        self.status = status
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the part to a dictionary for serialization
        
        Returns:
            Dictionary representation of the part
        """
        return {
            'id': self.part_id,
            'jobId': self.job_id,
            'partNumber': self.part_number,
            'machineId': self.machine_id,
            'startTime': self.start_time,
            'estimate': self.estimate,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Part':
        """
        Create a part from a dictionary
        
        Args:
            data: Dictionary representation of a part
            
        Returns:
            Part instance
        """
        return cls(
            part_id=data.get('id'),
            job_id=data.get('jobId', ''),
            part_number=data.get('partNumber', 1),
            machine_id=data.get('machineId'),
            start_time=data.get('startTime', 0),
            estimate=data.get('estimate', True),
            status=data.get('status', 'scheduled')
        )
    
    def get_end_time(self, cycle_time: float) -> int:
        """
        Calculate the end time of the part based on start time and cycle time
        
        Args:
            cycle_time: Cycle time in minutes
            
        Returns:
            End time as timestamp in milliseconds
        """
        # Convert cycle time from minutes to milliseconds
        cycle_time_ms = int(cycle_time * 60 * 1000)
        return self.start_time + cycle_time_ms
    
    def overlaps_with(self, other: 'Part', cycle_time: float) -> bool:
        """
        Check if this part overlaps with another part
        
        Args:
            other: Another part to check for overlap
            cycle_time: Cycle time in minutes
            
        Returns:
            True if the parts overlap, False otherwise
        """
        if self.machine_id != other.machine_id:
            return False
            
        self_end = self.get_end_time(cycle_time)
        other_end = other.get_end_time(cycle_time)
        
        # Check for overlap
        return (self.start_time < other_end and self_end > other.start_time)