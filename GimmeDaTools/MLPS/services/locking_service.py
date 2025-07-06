"""
Locking Service for dual lock management (Scheduler + JMS)
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Literal

from models.scheduler_lock import SchedulerLock
from models.job import Job
from utils.event_system import event_system
from utils.file_utils import load_json_file, save_json_file


class LockingService:
    """
    Service for managing scheduler locks independent from JMS locks
    """
    def __init__(
        self,
        locks_database_path: str = "scheduler_locks.json"
    ):
        """
        Initialize the locking service
        
        Args:
            locks_database_path: Path to the scheduler locks database JSON file
        """
        self.locks_database_path = locks_database_path
        self.locks: Dict[str, SchedulerLock] = {}
        
        self.load_database()
        
        # Start background cleanup of expired locks
        self._schedule_cleanup()
        
    def load_database(self) -> None:
        """Load scheduler locks from database file"""
        locks_data = load_json_file(self.locks_database_path, default={})
        self.locks = {
            lock_id: SchedulerLock.from_dict(lock_data)
            for lock_id, lock_data in locks_data.items()
        }
        
        # Clean up expired locks on load
        self._cleanup_expired_locks()
        
        event_system.publish("scheduler_locks_loaded", self.locks)
        
    def save_database(self) -> None:
        """Save scheduler locks to database file"""
        locks_data = {
            lock_id: lock.to_dict()
            for lock_id, lock in self.locks.items()
        }
        success = save_json_file(self.locks_database_path, locks_data)
        
        if success:
            event_system.publish("scheduler_locks_saved", self.locks)
        else:
            event_system.publish("error", "Failed to save scheduler locks data")
    
    # Lock Management
    def apply_scheduler_lock(
        self,
        job_id: str,
        lock_type: Literal['schedule_arrangement', 'full_edit'] = 'schedule_arrangement',
        locked_by: str = "user",
        duration_minutes: Optional[int] = None,
        reason: str = ""
    ) -> SchedulerLock:
        """
        Apply a scheduler lock to a job
        
        Args:
            job_id: ID of the job to lock
            lock_type: Type of lock to apply
            locked_by: User applying the lock
            duration_minutes: Lock duration (None for permanent)
            reason: Reason for the lock
            
        Returns:
            Created SchedulerLock
        """
        # Remove any existing lock for this job
        self.remove_scheduler_lock(job_id)
        
        # Create new lock
        if duration_minutes is not None:
            lock = SchedulerLock.create_temporary_lock(
                job_id=job_id,
                locked_by=locked_by,
                duration_minutes=duration_minutes,
                reason=reason or f"Temporary {lock_type} lock"
            )
        else:
            lock = SchedulerLock.create_permanent_lock(
                job_id=job_id,
                locked_by=locked_by,
                lock_type=lock_type,
                reason=reason or f"Permanent {lock_type} lock"
            )
        
        lock.lock_type = lock_type
        self.locks[lock.lock_id] = lock
        self.save_database()
        
        event_system.publish("scheduler_lock_applied", lock)
        return lock
    
    def remove_scheduler_lock(self, job_id: str) -> bool:
        """
        Remove scheduler lock from a job
        
        Args:
            job_id: ID of the job to unlock
            
        Returns:
            True if lock was removed
        """
        # Find lock for this job
        lock_to_remove = None
        for lock in self.locks.values():
            if lock.job_id == job_id:
                lock_to_remove = lock
                break
        
        if lock_to_remove:
            del self.locks[lock_to_remove.lock_id]
            self.save_database()
            event_system.publish("scheduler_lock_removed", job_id, lock_to_remove)
            return True
        
        return False
    
    def get_job_lock(self, job_id: str) -> Optional[SchedulerLock]:
        """
        Get the scheduler lock for a job
        
        Args:
            job_id: ID of the job
            
        Returns:
            SchedulerLock if exists and not expired, None otherwise
        """
        for lock in self.locks.values():
            if lock.job_id == job_id and not lock.is_expired():
                return lock
        return None
    
    def is_job_locked(self, job_id: str) -> bool:
        """
        Check if a job has an active scheduler lock
        
        Args:
            job_id: ID of the job
            
        Returns:
            True if job is locked by scheduler
        """
        return self.get_job_lock(job_id) is not None
    
    def can_rearrange_job(self, job_id: str) -> bool:
        """
        Check if a job can be rearranged (not locked by scheduler)
        
        Args:
            job_id: ID of the job
            
        Returns:
            True if job can be rearranged
        """
        lock = self.get_job_lock(job_id)
        return lock is None or not lock.prevents_rearrangement()
    
    def can_edit_job(self, job_id: str) -> bool:
        """
        Check if a job can be edited (not locked by full_edit scheduler lock)
        
        Args:
            job_id: ID of the job
            
        Returns:
            True if job can be edited
        """
        lock = self.get_job_lock(job_id)
        return lock is None or not lock.prevents_editing()
    
    def get_lock_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get comprehensive lock status for a job
        
        Args:
            job_id: ID of the job
            
        Returns:
            Dictionary with lock status information
        """
        scheduler_lock = self.get_job_lock(job_id)
        
        status = {
            'job_id': job_id,
            'scheduler_locked': scheduler_lock is not None,
            'can_rearrange': self.can_rearrange_job(job_id),
            'can_edit': self.can_edit_job(job_id),
            'scheduler_lock_info': scheduler_lock.to_dict() if scheduler_lock else None
        }
        
        return status
    
    def get_all_locks(self) -> Dict[str, SchedulerLock]:
        """Get all active scheduler locks"""
        # Clean up expired locks first
        self._cleanup_expired_locks()
        return self.locks.copy()
    
    def get_locks_by_user(self, locked_by: str) -> List[SchedulerLock]:
        """
        Get all locks created by a specific user
        
        Args:
            locked_by: User who created the locks
            
        Returns:
            List of locks created by the user
        """
        return [
            lock for lock in self.locks.values()
            if lock.locked_by == locked_by and not lock.is_expired()
        ]
    
    def extend_lock(self, job_id: str, additional_minutes: int) -> bool:
        """
        Extend an existing lock
        
        Args:
            job_id: ID of the job
            additional_minutes: Minutes to add to the lock
            
        Returns:
            True if lock was extended
        """
        lock = self.get_job_lock(job_id)
        if lock:
            lock.extend_lock(additional_minutes)
            self.save_database()
            event_system.publish("scheduler_lock_extended", lock)
            return True
        return False
    
    # Bulk Operations
    def bulk_lock_jobs(
        self,
        job_ids: List[str],
        lock_type: Literal['schedule_arrangement', 'full_edit'] = 'schedule_arrangement',
        locked_by: str = "user",
        duration_minutes: Optional[int] = None,
        reason: str = ""
    ) -> Dict[str, bool]:
        """
        Apply scheduler locks to multiple jobs
        
        Args:
            job_ids: List of job IDs to lock
            lock_type: Type of lock to apply
            locked_by: User applying the locks
            duration_minutes: Lock duration (None for permanent)
            reason: Reason for the locks
            
        Returns:
            Dictionary mapping job_id to success status
        """
        results = {}
        reason = reason or f"Bulk {lock_type} lock"
        
        for job_id in job_ids:
            try:
                self.apply_scheduler_lock(
                    job_id=job_id,
                    lock_type=lock_type,
                    locked_by=locked_by,
                    duration_minutes=duration_minutes,
                    reason=reason
                )
                results[job_id] = True
            except Exception as e:
                event_system.publish("error", f"Failed to lock job {job_id}: {str(e)}")
                results[job_id] = False
        
        event_system.publish("bulk_scheduler_locks_applied", results)
        return results
    
    def bulk_unlock_jobs(self, job_ids: List[str]) -> Dict[str, bool]:
        """
        Remove scheduler locks from multiple jobs
        
        Args:
            job_ids: List of job IDs to unlock
            
        Returns:
            Dictionary mapping job_id to success status
        """
        results = {}
        
        for job_id in job_ids:
            results[job_id] = self.remove_scheduler_lock(job_id)
        
        event_system.publish("bulk_scheduler_locks_removed", results)
        return results
    
    def unlock_all_user_locks(self, locked_by: str) -> int:
        """
        Remove all locks created by a specific user
        
        Args:
            locked_by: User whose locks to remove
            
        Returns:
            Number of locks removed
        """
        user_locks = self.get_locks_by_user(locked_by)
        count = 0
        
        for lock in user_locks:
            if self.remove_scheduler_lock(lock.job_id):
                count += 1
        
        event_system.publish("user_scheduler_locks_cleared", locked_by, count)
        return count
    
    # Integration with JMS Status
    def get_combined_lock_status(self, job: Job, jms_service=None) -> Dict[str, Any]:
        """
        Get combined lock status including both scheduler and JMS locks
        
        Args:
            job: Job to check
            jms_service: Optional JMS service for checking JMS lock status
            
        Returns:
            Combined lock status information
        """
        scheduler_status = self.get_lock_status(job.job_id)
        
        # Check JMS lock status
        jms_locked = False
        jms_lock_info = None
        
        if jms_service and hasattr(job, 'status'):
            jms_locked = job.status == 'locked'
            if jms_locked:
                jms_lock_info = {
                    'type': 'jms_production_lock',
                    'status': job.status,
                    'description': 'Job is locked in JMS production system'
                }
        
        combined_status = {
            **scheduler_status,
            'jms_locked': jms_locked,
            'jms_lock_info': jms_lock_info,
            'any_lock_active': scheduler_status['scheduler_locked'] or jms_locked,
            'lock_summary': self._generate_lock_summary(
                scheduler_status['scheduler_locked'],
                jms_locked,
                scheduler_status.get('scheduler_lock_info')
            )
        }
        
        return combined_status
    
    def _generate_lock_summary(
        self, 
        scheduler_locked: bool, 
        jms_locked: bool, 
        scheduler_info: Optional[Dict[str, Any]]
    ) -> str:
        """Generate human-readable lock summary"""
        if not scheduler_locked and not jms_locked:
            return "🔓 Unlocked - Full editing and rearrangement allowed"
        elif scheduler_locked and not jms_locked:
            lock_type = scheduler_info.get('lockType', 'unknown') if scheduler_info else 'unknown'
            if lock_type == 'schedule_arrangement':
                return "🔒 Scheduler Locked - No rearrangement, JMS sync continues"
            else:
                return "🔒 Scheduler Locked - Full edit lock, JMS sync continues"
        elif not scheduler_locked and jms_locked:
            return "🏭 JMS Locked - Production locked in JMS, local changes allowed"
        else:
            return "🔐 Both Locked - Scheduler and JMS locks active"
    
    # Maintenance and Cleanup
    def _cleanup_expired_locks(self) -> int:
        """
        Remove expired locks from memory and database
        
        Returns:
            Number of locks removed
        """
        expired_locks = [
            lock_id for lock_id, lock in self.locks.items()
            if lock.is_expired()
        ]
        
        for lock_id in expired_locks:
            lock = self.locks.pop(lock_id)
            event_system.publish("scheduler_lock_expired", lock)
        
        if expired_locks:
            self.save_database()
        
        return len(expired_locks)
    
    def _schedule_cleanup(self) -> None:
        """Schedule periodic cleanup of expired locks"""
        # This would typically use a background thread or timer
        # For now, cleanup is called manually when needed
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get lock statistics
        
        Returns:
            Dictionary with lock statistics
        """
        active_locks = [lock for lock in self.locks.values() if not lock.is_expired()]
        
        stats = {
            'total_active_locks': len(active_locks),
            'arrangement_locks': len([l for l in active_locks if l.lock_type == 'schedule_arrangement']),
            'full_edit_locks': len([l for l in active_locks if l.lock_type == 'full_edit']),
            'permanent_locks': len([l for l in active_locks if l.expires_at is None]),
            'temporary_locks': len([l for l in active_locks if l.expires_at is not None]),
            'locks_by_user': {}
        }
        
        # Count locks by user
        for lock in active_locks:
            user = lock.locked_by
            stats['locks_by_user'][user] = stats['locks_by_user'].get(user, 0) + 1
        
        return stats