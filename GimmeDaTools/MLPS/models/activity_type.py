"""
Activity Type model for scheduler machine bookings
"""
from datetime import datetime
from typing import Dict, Any, Optional, Literal
import uuid


class ActivityType:
    """
    Represents a type of activity that can be scheduled on machines
    """
    def __init__(
        self,
        type_id: Optional[str] = None,
        name: str = "",
        color: str = "#6b7280",  # Default gray
        blocking_type: Literal['complete', 'flexible', 'none'] = 'complete',
        default_duration: int = 60,  # minutes
        requires_approval: bool = False,
        icon: str = "🔧",
        description: str = "",
        created_at: Optional[int] = None
    ):
        """
        Initialize an activity type
        
        Args:
            type_id: Unique identifier for the activity type
            name: Display name of the activity type
            color: Color code for visual representation
            blocking_type: How this activity affects production jobs
            default_duration: Default duration in minutes
            requires_approval: Whether this activity requires supervisor approval
            icon: Unicode icon for display
            description: Detailed description of the activity
            created_at: Creation timestamp in milliseconds
        """
        self.type_id = type_id or f"activity-{uuid.uuid4()}"
        self.name = name
        self.color = color
        self.blocking_type = blocking_type
        self.default_duration = default_duration
        self.requires_approval = requires_approval
        self.icon = icon
        self.description = description
        self.created_at = created_at or int(datetime.now().timestamp() * 1000)
        
    def blocks_production(self) -> bool:
        """
        Check if this activity type blocks production
        
        Returns:
            True if production jobs cannot run during this activity
        """
        return self.blocking_type == 'complete'
    
    def allows_flexible_scheduling(self) -> bool:
        """
        Check if production jobs can be flexibly scheduled around this activity
        
        Returns:
            True if jobs can be rescheduled around this activity
        """
        return self.blocking_type == 'flexible'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the activity type to a dictionary for serialization
        
        Returns:
            Dictionary representation of the activity type
        """
        return {
            'id': self.type_id,
            'name': self.name,
            'color': self.color,
            'blockingType': self.blocking_type,
            'defaultDuration': self.default_duration,
            'requiresApproval': self.requires_approval,
            'icon': self.icon,
            'description': self.description,
            'createdAt': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityType':
        """
        Create an activity type from a dictionary
        
        Args:
            data: Dictionary representation of an activity type
            
        Returns:
            ActivityType instance
        """
        return cls(
            type_id=data.get('id'),
            name=data.get('name', ''),
            color=data.get('color', '#6b7280'),
            blocking_type=data.get('blockingType', 'complete'),
            default_duration=data.get('defaultDuration', 60),
            requires_approval=data.get('requiresApproval', False),
            icon=data.get('icon', '🔧'),
            description=data.get('description', ''),
            created_at=data.get('createdAt')
        )
    
    @classmethod
    def create_default_types(cls) -> Dict[str, 'ActivityType']:
        """
        Create a set of default activity types
        
        Returns:
            Dictionary of default activity types
        """
        defaults = {
            'setup': cls(
                type_id='setup',
                name='Machine Setup',
                color='#f59e0b',  # amber
                blocking_type='complete',
                default_duration=30,
                requires_approval=False,
                icon='⚙️',
                description='Initial machine setup and preparation'
            ),
            'maintenance': cls(
                type_id='maintenance',
                name='Scheduled Maintenance',
                color='#ef4444',  # red
                blocking_type='complete',
                default_duration=120,
                requires_approval=True,
                icon='🔧',
                description='Scheduled maintenance and repairs'
            ),
            'tool_change': cls(
                type_id='tool_change',
                name='Tool Change',
                color='#8b5cf6',  # violet
                blocking_type='flexible',
                default_duration=15,
                requires_approval=False,
                icon='🔄',
                description='Tool replacement and calibration'
            ),
            'cleaning': cls(
                type_id='cleaning',
                name='Machine Cleaning',
                color='#06b6d4',  # cyan
                blocking_type='flexible',
                default_duration=45,
                requires_approval=False,
                icon='🧹',
                description='Routine machine cleaning and inspection'
            ),
            'inspection': cls(
                type_id='inspection',
                name='Quality Inspection',
                color='#10b981',  # emerald
                blocking_type='none',
                default_duration=20,
                requires_approval=False,
                icon='🔍',
                description='Quality control and inspection activities'
            ),
            'break': cls(
                type_id='break',
                name='Operator Break',
                color='#6b7280',  # gray
                blocking_type='none',
                default_duration=15,
                requires_approval=False,
                icon='☕',
                description='Scheduled operator breaks'
            )
        }
        return defaults