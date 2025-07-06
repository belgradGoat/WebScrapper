"""
Workpiece Priority model for JMS integration
"""
from datetime import datetime
from typing import Dict, Any, Optional, Literal
import uuid


class WorkpiecePriority:
    """
    Represents workpiece priority for production scheduling and JMS integration
    """
    def __init__(
        self,
        priority_id: Optional[str] = None,
        job_id: str = "",
        priority_level: Literal['critical', 'high', 'normal', 'low'] = 'normal',
        priority_score: int = 50,  # 1-100 scale
        rush_order: bool = False,
        due_date: Optional[int] = None,  # timestamp in milliseconds
        customer_priority: bool = False,
        notes: str = "",
        updated_by: str = "system",
        updated_at: Optional[int] = None
    ):
        """
        Initialize workpiece priority
        
        Args:
            priority_id: Unique identifier for the priority record
            job_id: ID of the job this priority applies to
            priority_level: Priority level category
            priority_score: Numeric priority score (1-100, higher = more priority)
            rush_order: Whether this is a rush/urgent order
            due_date: Due date timestamp in milliseconds
            customer_priority: Whether customer has requested priority
            notes: Additional priority notes
            updated_by: User who last updated the priority
            updated_at: Last update timestamp in milliseconds
        """
        self.priority_id = priority_id or f"priority-{uuid.uuid4()}"
        self.job_id = job_id
        self.priority_level = priority_level
        self.priority_score = max(1, min(100, priority_score))  # Clamp to 1-100
        self.rush_order = rush_order
        self.due_date = due_date
        self.customer_priority = customer_priority
        self.notes = notes
        self.updated_by = updated_by
        self.updated_at = updated_at or int(datetime.now().timestamp() * 1000)
        
        # Auto-adjust priority score based on level
        self._sync_priority_score_with_level()
    
    def _sync_priority_score_with_level(self) -> None:
        """Synchronize priority score with priority level"""
        level_scores = {
            'critical': 90,
            'high': 75,
            'normal': 50,
            'low': 25
        }
        
        # Only auto-adjust if score is at default or matches another level
        if self.priority_score in [90, 75, 50, 25]:
            self.priority_score = level_scores.get(self.priority_level, 50)
    
    def is_overdue(self) -> bool:
        """
        Check if the job is overdue based on due date
        
        Returns:
            True if past due date
        """
        if self.due_date is None:
            return False
        return int(datetime.now().timestamp() * 1000) > self.due_date
    
    def get_days_until_due(self) -> Optional[int]:
        """
        Get number of days until due date
        
        Returns:
            Days until due (negative if overdue), None if no due date
        """
        if self.due_date is None:
            return None
        
        now = datetime.now().timestamp() * 1000
        diff_ms = self.due_date - now
        return int(diff_ms / (1000 * 60 * 60 * 24))
    
    def get_effective_priority_score(self) -> int:
        """
        Calculate effective priority score including rush and overdue factors
        
        Returns:
            Effective priority score (1-100)
        """
        score = self.priority_score
        
        # Rush order boost
        if self.rush_order:
            score = min(100, score + 20)
        
        # Customer priority boost
        if self.customer_priority:
            score = min(100, score + 10)
        
        # Overdue penalty (increases priority)
        if self.is_overdue():
            days_overdue = abs(self.get_days_until_due() or 0)
            overdue_boost = min(20, days_overdue * 2)  # Up to 20 point boost
            score = min(100, score + overdue_boost)
        
        return score
    
    def set_priority_level(self, level: Literal['critical', 'high', 'normal', 'low']) -> None:
        """
        Set priority level and update score accordingly
        
        Args:
            level: New priority level
        """
        self.priority_level = level
        self._sync_priority_score_with_level()
        self.updated_at = int(datetime.now().timestamp() * 1000)
    
    def promote_priority(self) -> bool:
        """
        Promote to next higher priority level
        
        Returns:
            True if promotion occurred
        """
        promotions = {
            'low': 'normal',
            'normal': 'high', 
            'high': 'critical'
        }
        
        if self.priority_level in promotions:
            self.set_priority_level(promotions[self.priority_level])
            return True
        return False
    
    def demote_priority(self) -> bool:
        """
        Demote to next lower priority level
        
        Returns:
            True if demotion occurred
        """
        demotions = {
            'critical': 'high',
            'high': 'normal',
            'normal': 'low'
        }
        
        if self.priority_level in demotions:
            self.set_priority_level(demotions[self.priority_level])
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert priority to dictionary for serialization
        
        Returns:
            Dictionary representation of the priority
        """
        return {
            'id': self.priority_id,
            'jobId': self.job_id,
            'priorityLevel': self.priority_level,
            'priorityScore': self.priority_score,
            'effectivePriorityScore': self.get_effective_priority_score(),
            'rushOrder': self.rush_order,
            'dueDate': self.due_date,
            'customerPriority': self.customer_priority,
            'notes': self.notes,
            'updatedBy': self.updated_by,
            'updatedAt': self.updated_at,
            'isOverdue': self.is_overdue(),
            'daysUntilDue': self.get_days_until_due()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkpiecePriority':
        """
        Create priority from dictionary
        
        Args:
            data: Dictionary representation of priority
            
        Returns:
            WorkpiecePriority instance
        """
        return cls(
            priority_id=data.get('id'),
            job_id=data.get('jobId', ''),
            priority_level=data.get('priorityLevel', 'normal'),
            priority_score=data.get('priorityScore', 50),
            rush_order=data.get('rushOrder', False),
            due_date=data.get('dueDate'),
            customer_priority=data.get('customerPriority', False),
            notes=data.get('notes', ''),
            updated_by=data.get('updatedBy', 'system'),
            updated_at=data.get('updatedAt')
        )
    
    @classmethod
    def create_rush_order(cls, job_id: str, due_date: Optional[int] = None) -> 'WorkpiecePriority':
        """
        Create a rush order priority
        
        Args:
            job_id: ID of the job
            due_date: Optional due date
            
        Returns:
            WorkpiecePriority configured as rush order
        """
        return cls(
            job_id=job_id,
            priority_level='high',
            priority_score=85,
            rush_order=True,
            due_date=due_date,
            notes="Rush order - expedited processing required"
        )
    
    @classmethod
    def create_standard_priority(cls, job_id: str) -> 'WorkpiecePriority':
        """
        Create a standard priority
        
        Args:
            job_id: ID of the job
            
        Returns:
            WorkpiecePriority with normal settings
        """
        return cls(
            job_id=job_id,
            priority_level='normal',
            priority_score=50,
            rush_order=False
        )