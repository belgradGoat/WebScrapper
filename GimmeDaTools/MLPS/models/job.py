"""
Job model for Machine Shop Scheduler
"""
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
import uuid


class Job:
    """
    Represents a manufacturing job with its properties and parts
    """
    def __init__(
        self,
        job_id: Optional[str] = None,
        name: str = "",
        total_parts: int = 1,
        cycle_time: float = 1.0,
        color: Optional[str] = None,
        created_at: Optional[int] = None,
        status: Literal['active', 'locked', 'error', 'completed', 'paused'] = 'active'
    ):
        """
        Initialize a job with its properties
        
        Args:
            job_id: Unique identifier for the job (generated if not provided)
            name: Display name of the job
            total_parts: Total number of parts in the job
            cycle_time: Cycle time per part in minutes
            color: Color for visual representation
            created_at: Creation timestamp
            status: Job status (active, locked, error, completed, paused)
        """
        self.job_id = job_id or f"job-{uuid.uuid4()}"
        self.name = name
        self.total_parts = total_parts
        self.cycle_time = cycle_time
        self.color = color or self._generate_color()
        self.created_at = created_at or int(datetime.now().timestamp() * 1000)
        self.status = status
        
    def _generate_color(self) -> str:
        """
        Generate a random color for the job
        
        Returns:
            Hex color code
        """
        # List of pleasant colors for jobs
        colors = [
            '#ef4444',  # red
            '#f97316',  # orange
            '#fbbf24',  # amber
            '#84cc16',  # lime
            '#22c55e',  # green
            '#10b981',  # emerald
            '#14b8a6',  # teal
            '#06b6d4',  # cyan
            '#0ea5e9',  # sky
            '#3b82f6',  # blue
            '#6366f1',  # indigo
            '#8b5cf6',  # violet
            '#a855f7',  # purple
            '#d946ef',  # fuchsia
            '#ec4899',  # pink
            '#f43f5e',  # rose
        ]
        
        # Use job_id to deterministically select a color
        hash_value = hash(self.job_id)
        index = abs(hash_value) % len(colors)
        return colors[index]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the job to a dictionary for serialization
        
        Returns:
            Dictionary representation of the job
        """
        return {
            'id': self.job_id,
            'name': self.name,
            'totalParts': self.total_parts,
            'cycleTime': self.cycle_time,
            'color': self.color,
            'createdAt': self.created_at,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """
        Create a job from a dictionary
        
        Args:
            data: Dictionary representation of a job
            
        Returns:
            Job instance
        """
        return cls(
            job_id=data.get('id'),
            name=data.get('name', ''),
            total_parts=data.get('totalParts', 1),
            cycle_time=data.get('cycleTime', 1.0),
            color=data.get('color'),
            created_at=data.get('createdAt'),
            status=data.get('status', 'active')
        )