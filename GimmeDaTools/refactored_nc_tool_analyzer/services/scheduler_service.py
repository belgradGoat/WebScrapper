"""
Scheduler Service for Machine Shop Scheduler
"""
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from models.job import Job
from models.part import Part
from models.machine import Machine
from utils.event_system import event_system
from utils.file_utils import load_json_file, save_json_file


class SchedulerService:
    """
    Service for managing jobs and parts scheduling
    """
    def __init__(
        self, 
        machine_service,
        jobs_database_path: str = "scheduler_jobs.json",
        parts_database_path: str = "scheduler_parts.json"
    ):
        """
        Initialize the scheduler service
        
        Args:
            machine_service: MachineService instance for accessing machine data
            jobs_database_path: Path to the jobs database JSON file
            parts_database_path: Path to the parts database JSON file
        """
        self.machine_service = machine_service
        self.jobs_database_path = jobs_database_path
        self.parts_database_path = parts_database_path
        
        self.jobs: Dict[str, Job] = {}
        self.parts: Dict[str, Part] = {}
        
        self.load_database()
        
    def load_database(self) -> None:
        """
        Load jobs and parts from the database files
        """
        # Load jobs
        jobs_data = load_json_file(self.jobs_database_path, default={})
        self.jobs = {job_id: Job.from_dict(job_data) for job_id, job_data in jobs_data.items()}
        
        # Load parts
        parts_data = load_json_file(self.parts_database_path, default={})
        self.parts = {part_id: Part.from_dict(part_data) for part_id, part_data in parts_data.items()}
        
        # Notify listeners that data was loaded
        event_system.publish("scheduler_data_loaded", self.jobs, self.parts)
        
    def save_database(self) -> None:
        """
        Save jobs and parts to the database files
        """
        # Save jobs
        jobs_data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
        jobs_saved = save_json_file(self.jobs_database_path, jobs_data)
        
        # Save parts
        parts_data = {part_id: part.to_dict() for part_id, part in self.parts.items()}
        parts_saved = save_json_file(self.parts_database_path, parts_data)
        
        if jobs_saved and parts_saved:
            # Notify listeners that data was saved
            event_system.publish("scheduler_data_saved", self.jobs, self.parts)
        else:
            event_system.publish("error", "Failed to save scheduler data")
            
    def get_all_jobs(self) -> Dict[str, Job]:
        """
        Get all jobs
        
        Returns:
            Dictionary of job_id to Job objects
        """
        return self.jobs
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Get a specific job by ID
        
        Args:
            job_id: ID of the job to get
            
        Returns:
            Job object or None if not found
        """
        return self.jobs.get(job_id)
    
    def add_job(self, job: Job) -> Job:
        """
        Add a new job
        
        Args:
            job: Job object to add
            
        Returns:
            Added job
        """
        self.jobs[job.job_id] = job
        self.save_database()
        event_system.publish("job_added", job)
        return job
    
    def update_job(self, job: Job) -> Job:
        """
        Update an existing job
        
        Args:
            job: Job object to update
            
        Returns:
            Updated job
        """
        self.jobs[job.job_id] = job
        self.save_database()
        event_system.publish("job_updated", job)
        return job
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and all its parts
        
        Args:
            job_id: ID of the job to delete
            
        Returns:
            True if the job was deleted, False if not found
        """
        if job_id not in self.jobs:
            return False
            
        # Delete the job
        job = self.jobs.pop(job_id)
        
        # Delete all parts belonging to the job
        parts_to_delete = [part_id for part_id, part in self.parts.items() if part.job_id == job_id]
        for part_id in parts_to_delete:
            self.parts.pop(part_id)
            
        self.save_database()
        event_system.publish("job_deleted", job_id)
        return True
    
    def get_job_parts(self, job_id: str) -> List[Part]:
        """
        Get all parts for a specific job
        
        Args:
            job_id: ID of the job
            
        Returns:
            List of parts belonging to the job, sorted by part number
        """
        job_parts = [part for part in self.parts.values() if part.job_id == job_id]
        return sorted(job_parts, key=lambda p: p.part_number)
    
    def get_all_parts(self) -> Dict[str, Part]:
        """
        Get all parts
        
        Returns:
            Dictionary of part_id to Part objects
        """
        return self.parts
    
    def get_part(self, part_id: str) -> Optional[Part]:
        """
        Get a specific part by ID
        
        Args:
            part_id: ID of the part to get
            
        Returns:
            Part object or None if not found
        """
        return self.parts.get(part_id)
    
    def add_part(self, part: Part) -> Part:
        """
        Add a new part
        
        Args:
            part: Part object to add
            
        Returns:
            Added part
        """
        self.parts[part.part_id] = part
        self.save_database()
        event_system.publish("part_added", part)
        return part
    
    def update_part(self, part: Part) -> Part:
        """
        Update an existing part
        
        Args:
            part: Part object to update
            
        Returns:
            Updated part
        """
        self.parts[part.part_id] = part
        self.save_database()
        event_system.publish("part_updated", part)
        return part
    
    def delete_part(self, part_id: str) -> bool:
        """
        Delete a part
        
        Args:
            part_id: ID of the part to delete
            
        Returns:
            True if the part was deleted, False if not found
        """
        if part_id not in self.parts:
            return False
            
        part = self.parts.pop(part_id)
        
        # Update part numbers for remaining parts in the job
        job_parts = self.get_job_parts(part.job_id)
        for i, job_part in enumerate(job_parts, 1):
            if job_part.part_number > part.part_number:
                job_part.part_number -= 1
                self.parts[job_part.part_id] = job_part
        
        # Update job total parts
        job = self.get_job(part.job_id)
        if job:
            job.total_parts -= 1
            if job.total_parts <= 0:
                # If no parts left, delete the job
                self.delete_job(job.job_id)
            else:
                self.jobs[job.job_id] = job
        
        self.save_database()
        event_system.publish("part_deleted", part_id)
        return True
    
    def create_job_with_parts(
        self,
        name: str,
        machine_id: str,
        total_parts: int,
        cycle_time: float,
        start_date: str,
        start_hour: int,
        start_minute: int
    ) -> Job:
        """
        Create a new job with parts
        
        Args:
            name: Name of the job
            machine_id: ID of the machine for initial parts
            total_parts: Total number of parts
            cycle_time: Cycle time per part in minutes
            start_date: Start date in ISO format (YYYY-MM-DD)
            start_hour: Start hour (0-23)
            start_minute: Start minute (0-59)
            
        Returns:
            Created job
        """
        # Create the job
        job = Job(name=name, total_parts=total_parts, cycle_time=cycle_time)
        self.jobs[job.job_id] = job
        
        # Parse date string to avoid timezone issues
        date_parts = start_date.split('-')
        start_datetime = datetime(
            int(date_parts[0]),  # year
            int(date_parts[1]),  # month
            int(date_parts[2]),  # day
            start_hour,
            start_minute,
            0,
            0
        )
        current_time = int(start_datetime.timestamp() * 1000)  # Convert to milliseconds
        
        # Create parts for the job
        for i in range(total_parts):
            part = Part(
                job_id=job.job_id,
                part_number=i + 1,
                machine_id=machine_id,
                start_time=current_time,
                estimate=True,
                status='scheduled'
            )
            self.parts[part.part_id] = part
            
            # Add cycle time for next part
            current_time += int(job.cycle_time * 60 * 1000)  # Convert minutes to milliseconds
        
        self.save_database()
        event_system.publish("job_created_with_parts", job)
        return job
    
    def move_part(self, part_id: str, machine_id: str, start_time: int) -> bool:
        """
        Move a part to a different machine or time
        
        Args:
            part_id: ID of the part to move
            machine_id: ID of the target machine
            start_time: New start time in milliseconds
            
        Returns:
            True if the part was moved successfully, False otherwise
        """
        part = self.get_part(part_id)
        if not part:
            return False
            
        job = self.get_job(part.job_id)
        if not job:
            return False
            
        # Check for conflicts with other parts on the same machine
        conflicts = self._find_conflicts(part_id, machine_id, start_time, job.cycle_time)
        
        # Update the part
        old_machine_id = part.machine_id
        old_start_time = part.start_time
        
        part.machine_id = machine_id
        part.start_time = start_time
        self.parts[part_id] = part
        
        # Resolve conflicts by moving conflicting parts
        if conflicts:
            self._resolve_conflicts(conflicts, job.cycle_time)
        
        self.save_database()
        event_system.publish("part_moved", part, old_machine_id, old_start_time)
        return True
    
    def _find_conflicts(
        self,
        part_id: str,
        machine_id: str,
        start_time: int,
        cycle_time: float
    ) -> List[Part]:
        """
        Find parts that conflict with the given parameters
        
        Args:
            part_id: ID of the part being moved (to exclude from conflicts)
            machine_id: Target machine ID
            start_time: Target start time
            cycle_time: Cycle time in minutes
            
        Returns:
            List of conflicting parts
        """
        end_time = start_time + int(cycle_time * 60 * 1000)
        
        conflicts = []
        for other_part in self.parts.values():
            # Skip the part being moved
            if other_part.part_id == part_id:
                continue
                
            # Skip parts on different machines
            if other_part.machine_id != machine_id:
                continue
                
            # Get the job for this part
            other_job = self.get_job(other_part.job_id)
            if not other_job:
                continue
                
            other_end_time = other_part.start_time + int(other_job.cycle_time * 60 * 1000)
            
            # Check for overlap
            if other_part.start_time < end_time and other_end_time > start_time:
                conflicts.append(other_part)
        
        # Sort conflicts by start time
        conflicts.sort(key=lambda p: p.start_time)
        return conflicts
    
    def _resolve_conflicts(self, conflicts: List[Part], moved_part_cycle_time: float) -> None:
        """
        Resolve conflicts by moving conflicting parts
        
        Args:
            conflicts: List of conflicting parts
            moved_part_cycle_time: Cycle time of the moved part in minutes
        """
        # Calculate the end time of the moved part
        first_conflict = conflicts[0]
        moved_part_end_time = first_conflict.start_time + int(moved_part_cycle_time * 60 * 1000)
        
        # Move each conflicting part to start after the previous part
        next_start_time = moved_part_end_time
        
        for part in conflicts:
            job = self.get_job(part.job_id)
            if not job:
                continue
                
            # Update the part's start time
            part.start_time = next_start_time
            self.parts[part.part_id] = part
            
            # Calculate the next available start time
            next_start_time += int(job.cycle_time * 60 * 1000)
    
    def get_machine_utilization(self, machine_id: str, week_start: int) -> float:
        """
        Calculate machine utilization for a week
        
        Args:
            machine_id: ID of the machine
            week_start: Start time of the week in milliseconds
            
        Returns:
            Utilization percentage (0-100)
        """
        week_end = week_start + 7 * 24 * 60 * 60 * 1000
        
        # Get parts scheduled on this machine during the week
        week_parts = [
            part for part in self.parts.values()
            if part.machine_id == machine_id and part.start_time >= week_start and part.start_time < week_end
        ]
        
        # Calculate total minutes
        total_minutes = 0
        for part in week_parts:
            job = self.get_job(part.job_id)
            if job:
                total_minutes += job.cycle_time
        
        # Total minutes in a week
        week_minutes = 7 * 24 * 60
        
        # Calculate utilization percentage
        return (total_minutes / week_minutes) * 100 if week_minutes > 0 else 0
    
    def get_parts_for_day(self, machine_id: str, day_start: int) -> List[Part]:
        """
        Get parts scheduled on a machine for a specific day
        
        Args:
            machine_id: ID of the machine
            day_start: Start time of the day in milliseconds
            
        Returns:
            List of parts scheduled for the day
        """
        day_end = day_start + 24 * 60 * 60 * 1000
        
        day_parts = []
        for part in self.parts.values():
            if part.machine_id != machine_id:
                continue
                
            job = self.get_job(part.job_id)
            if not job:
                continue
                
            part_end = part.start_time + int(job.cycle_time * 60 * 1000)
            
            # Include parts that:
            # 1. Start during the day
            # 2. End during the day
            # 3. Span the entire day
            if ((part.start_time >= day_start and part.start_time < day_end) or
                (part_end > day_start and part_end <= day_end) or
                (part.start_time < day_start and part_end > day_end)):
                day_parts.append(part)
        
        return day_parts
    
    def duplicate_part(self, part_id: str) -> Optional[Part]:
        """
        Duplicate a part
        
        Args:
            part_id: ID of the part to duplicate
            
        Returns:
            Duplicated part or None if the original part was not found
        """
        original_part = self.get_part(part_id)
        if not original_part:
            return None
            
        job = self.get_job(original_part.job_id)
        if not job:
            return None
            
        # Get the highest part number for this job
        job_parts = self.get_job_parts(job.job_id)
        new_part_number = max(part.part_number for part in job_parts) + 1
        
        # Create the new part
        new_part = Part(
            job_id=original_part.job_id,
            part_number=new_part_number,
            machine_id=original_part.machine_id,
            start_time=original_part.start_time + int(job.cycle_time * 60 * 1000),
            estimate=original_part.estimate,
            status=original_part.status
        )
        
        # Add the part
        self.parts[new_part.part_id] = new_part
        
        # Update job total parts
        job.total_parts += 1
        self.jobs[job.job_id] = job
        
        self.save_database()
        event_system.publish("part_duplicated", new_part, original_part)
        return new_part