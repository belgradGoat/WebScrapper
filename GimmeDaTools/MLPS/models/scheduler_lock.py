"""
Scheduler Lock model for dual locking system
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Literal
import uuid


class SchedulerLock:
    """
    Represents a scheduler lock that prevents job rearrangement
    Independent from JMS production locks
    """
    def __init__(
        self,
        lock_id: Optional[str] = None,
        job_id: str = "",
        lock_type: Literal['schedule_arrangement', 'full_edit'] = 'schedule_arrangement',
        locked_by: str = "system",
        expires_at: Optional[int] = None,
        reason: str = "",
        created_at: Optional[int] = None
    ):
        """
        Initialize a scheduler lock
        
        Args:
            lock_id: Unique identifier for the lock
            job_id: ID of the job being locked
            lock_type: Type of lock (schedule_arrangement or full_edit)
            locked_by: User who applied the lock
            expires_at: Expiration timestamp in milliseconds (None for no expiration)
            reason: Reason for the lock
            created_at: Creation timestamp in milliseconds
        """
        self.lock_id = lock_id or f"lock-{uuid.uuid4()}"
        self.job_id = job_id
        self.lock_type = lock_type
        self.locked_by = locked_by
        self.expires_at = expires_at
        self.reason = reason
        self.created_at = created_at or int(datetime.now().timestamp() * 1000)
        
    def is_expired(self) -> bool:
        """
        Check if the lock has expired
        
        Returns:
            True if the lock has expired
        """
        if self.expires_at is None:
            return False
        return int(datetime.now().timestamp() * 1000) > self.expires_at
    
    def prevents_rearrangement(self) -> bool:
        """
        Check if this lock prevents job/part rearrangement
        
        Returns:
            True if rearrangement is blocked
        """
        return not self.is_expired()
    
    def prevents_editing(self) -> bool:
        """
        Check if this lock prevents job editing
        
        Returns:
            True if editing is blocked (only for full_edit locks)
        """
        return self.lock_type == 'full_edit' and not self.is_expired()
    
    def get_remaining_time_minutes(self) -> Optional[int]:
        """
        Get remaining time until lock expires
        
        Returns:
            Minutes remaining, or None if no expiration
        """
        if self.expires_at is None:
            return None
        
        now = int(datetime.now().timestamp() * 1000)
        if now >= self.expires_at:
            return 0
        
        remaining_ms = self.expires_at - now
        return int(remaining_ms / (1000 * 60))
    
    def extend_lock(self, additional_minutes: int) -> None:
        """
        Extend the lock by additional minutes
        
        Args:
            additional_minutes: Minutes to add to the lock
        """
        if self.expires_at is None:
            # If no expiration, set it to now + additional time
            self.expires_at = int(datetime.now().timestamp() * 1000) + (additional_minutes * 60 * 1000)
        else:
            # Add to existing expiration
            self.expires_at += (additional_minutes * 60 * 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the lock to a dictionary for serialization
        
        Returns:
            Dictionary representation of the lock
        """
        return {
            'id': self.lock_id,
            'jobId': self.job_id,
            'lockType': self.lock_type,
            'lockedBy': self.locked_by,
            'expiresAt': self.expires_at,
            'reason': self.reason,
            'createdAt': self.created_at,
            'isExpired': self.is_expired(),
            'remainingMinutes': self.get_remaining_time_minutes()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchedulerLock':
        """
        Create a lock from a dictionary
        
        Args:
            data: Dictionary representation of a lock
            
        Returns:
            SchedulerLock instance
        """
        return cls(
            lock_id=data.get('id'),
            job_id=data.get('jobId', ''),
            lock_type=data.get('lockType', 'schedule_arrangement'),
            locked_by=data.get('lockedBy', 'system'),
            expires_at=data.get('expiresAt'),
            reason=data.get('reason', ''),
            created_at=data.get('createdAt')
        )
    
    @classmethod
    def create_temporary_lock(
        cls, 
        job_id: str, 
        locked_by: str, 
        duration_minutes: int = 60,
        reason: str = "Temporary lock"
    ) -> 'SchedulerLock':
        """
        Create a temporary lock that expires after specified minutes
        
        Args:
            job_id: ID of the job to lock
            locked_by: User applying the lock
            duration_minutes: Duration in minutes
            reason: Reason for the lock
            
        Returns:
            SchedulerLock instance with expiration
        """
        expires_at = int((datetime.now() + timedelta(minutes=duration_minutes)).timestamp() * 1000)
        return cls(
            job_id=job_id,
            locked_by=locked_by,
            expires_at=expires_at,
            reason=reason
        )
    
    @classmethod
    def create_permanent_lock(
        cls,
        job_id: str,
        locked_by: str,
        lock_type: Literal['schedule_arrangement', 'full_edit'] = 'schedule_arrangement',
        reason: str = "Permanent lock"
    ) -> 'SchedulerLock':
        """
        Create a permanent lock that doesn't expire
        
        Args:
            job_id: ID of the job to lock
            locked_by: User applying the lock
            lock_type: Type of lock to apply
            reason: Reason for the lock
            
        Returns:
            SchedulerLock instance without expiration
        """
        return cls(
            job_id=job_id,
            lock_type=lock_type,
            locked_by=locked_by,
            expires_at=None,
            reason=reason
        )