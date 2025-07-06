"""
Machine Booking model for scheduler
"""
from datetime import datetime
from typing import Dict, Any, Optional, Literal
import uuid


class MachineBooking:
    """
    Represents a machine booking for maintenance, setup, or other activities
    """
    def __init__(
        self,
        booking_id: Optional[str] = None,
        machine_id: str = "",
        activity_type_id: str = "",
        start_time: int = 0,
        duration: int = 60,  # minutes
        description: str = "",
        blocking_type: Literal['complete', 'flexible', 'none'] = 'complete',
        created_by: str = "system",
        created_at: Optional[int] = None
    ):
        """
        Initialize a machine booking
        
        Args:
            booking_id: Unique identifier for the booking
            machine_id: ID of the machine being booked
            activity_type_id: ID of the activity type
            start_time: Start time as timestamp in milliseconds
            duration: Duration in minutes
            description: Description of the booking
            blocking_type: How this booking affects production jobs
            created_by: User who created the booking
            created_at: Creation timestamp in milliseconds
        """
        self.booking_id = booking_id or f"booking-{uuid.uuid4()}"
        self.machine_id = machine_id
        self.activity_type_id = activity_type_id
        self.start_time = start_time
        self.duration = duration
        self.description = description
        self.blocking_type = blocking_type
        self.created_by = created_by
        self.created_at = created_at or int(datetime.now().timestamp() * 1000)
        
    def get_end_time(self) -> int:
        """
        Calculate the end time of the booking
        
        Returns:
            End time as timestamp in milliseconds
        """
        return self.start_time + (self.duration * 60 * 1000)
    
    def overlaps_with_time_range(self, start: int, end: int) -> bool:
        """
        Check if this booking overlaps with a given time range
        
        Args:
            start: Start time in milliseconds
            end: End time in milliseconds
            
        Returns:
            True if there's an overlap
        """
        booking_end = self.get_end_time()
        return (self.start_time < end and booking_end > start)
    
    def conflicts_with_production(self) -> bool:
        """
        Check if this booking blocks production jobs
        
        Returns:
            True if production jobs cannot run during this booking
        """
        return self.blocking_type == 'complete'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the booking to a dictionary for serialization
        
        Returns:
            Dictionary representation of the booking
        """
        return {
            'id': self.booking_id,
            'machineId': self.machine_id,
            'activityTypeId': self.activity_type_id,
            'startTime': self.start_time,
            'duration': self.duration,
            'description': self.description,
            'blockingType': self.blocking_type,
            'createdBy': self.created_by,
            'createdAt': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MachineBooking':
        """
        Create a booking from a dictionary
        
        Args:
            data: Dictionary representation of a booking
            
        Returns:
            MachineBooking instance
        """
        return cls(
            booking_id=data.get('id'),
            machine_id=data.get('machineId', ''),
            activity_type_id=data.get('activityTypeId', ''),
            start_time=data.get('startTime', 0),
            duration=data.get('duration', 60),
            description=data.get('description', ''),
            blocking_type=data.get('blockingType', 'complete'),
            created_by=data.get('createdBy', 'system'),
            created_at=data.get('createdAt')
        )