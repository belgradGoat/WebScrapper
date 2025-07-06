"""
Machine Booking Service for scheduler
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional

from models.machine_booking import MachineBooking
from models.activity_type import ActivityType
from models.part import Part
from models.job import Job
from utils.event_system import event_system
from utils.file_utils import load_json_file, save_json_file


class MachineBookingService:
    """
    Service for managing machine bookings and activity types
    """
    def __init__(
        self,
        bookings_database_path: str = "machine_bookings.json",
        activity_types_database_path: str = "activity_types.json"
    ):
        """
        Initialize the machine booking service
        
        Args:
            bookings_database_path: Path to the bookings database JSON file
            activity_types_database_path: Path to the activity types database JSON file
        """
        self.bookings_database_path = bookings_database_path
        self.activity_types_database_path = activity_types_database_path
        
        self.bookings: Dict[str, MachineBooking] = {}
        self.activity_types: Dict[str, ActivityType] = {}
        
        self.load_database()
        
    def load_database(self) -> None:
        """Load bookings and activity types from database files"""
        # Load bookings
        bookings_data = load_json_file(self.bookings_database_path, default={})
        self.bookings = {
            booking_id: MachineBooking.from_dict(booking_data)
            for booking_id, booking_data in bookings_data.items()
        }
        
        # Load activity types
        activity_types_data = load_json_file(self.activity_types_database_path, default={})
        if not activity_types_data:
            # Initialize with default activity types
            self.activity_types = ActivityType.create_default_types()
            self.save_activity_types()
        else:
            self.activity_types = {
                type_id: ActivityType.from_dict(type_data)
                for type_id, type_data in activity_types_data.items()
            }
        
        event_system.publish("booking_data_loaded", self.bookings, self.activity_types)
        
    def save_database(self) -> None:
        """Save bookings to database file"""
        bookings_data = {
            booking_id: booking.to_dict() 
            for booking_id, booking in self.bookings.items()
        }
        success = save_json_file(self.bookings_database_path, bookings_data)
        
        if success:
            event_system.publish("booking_data_saved", self.bookings)
        else:
            event_system.publish("error", "Failed to save machine booking data")
            
    def save_activity_types(self) -> None:
        """Save activity types to database file"""
        activity_types_data = {
            type_id: activity_type.to_dict()
            for type_id, activity_type in self.activity_types.items()
        }
        success = save_json_file(self.activity_types_database_path, activity_types_data)
        
        if success:
            event_system.publish("activity_types_saved", self.activity_types)
        else:
            event_system.publish("error", "Failed to save activity types data")
    
    # Machine Booking Management
    def create_booking(
        self,
        machine_id: str,
        activity_type_id: str,
        start_time: int,
        duration: Optional[int] = None,
        description: str = "",
        created_by: str = "user"
    ) -> MachineBooking:
        """
        Create a new machine booking
        
        Args:
            machine_id: ID of the machine to book
            activity_type_id: ID of the activity type
            start_time: Start time in milliseconds
            duration: Duration in minutes (uses activity type default if None)
            description: Booking description
            created_by: User creating the booking
            
        Returns:
            Created MachineBooking
            
        Raises:
            ValueError: If activity type not found or conflicts exist
        """
        # Get activity type
        activity_type = self.activity_types.get(activity_type_id)
        if not activity_type:
            raise ValueError(f"Activity type {activity_type_id} not found")
        
        # Use default duration if not specified
        if duration is None:
            duration = activity_type.default_duration
        
        # Create booking
        booking = MachineBooking(
            machine_id=machine_id,
            activity_type_id=activity_type_id,
            start_time=start_time,
            duration=duration,
            description=description,
            blocking_type=activity_type.blocking_type,
            created_by=created_by
        )
        
        # Check for conflicts if this is a blocking activity
        if booking.conflicts_with_production():
            conflicts = self.find_booking_conflicts(booking)
            if conflicts:
                event_system.publish("booking_conflicts_detected", booking, conflicts)
        
        # Save booking
        self.bookings[booking.booking_id] = booking
        self.save_database()
        
        event_system.publish("booking_created", booking)
        return booking
    
    def get_booking(self, booking_id: str) -> Optional[MachineBooking]:
        """Get a booking by ID"""
        return self.bookings.get(booking_id)
    
    def get_all_bookings(self) -> Dict[str, MachineBooking]:
        """Get all bookings"""
        return self.bookings
    
    def get_machine_bookings(
        self, 
        machine_id: str, 
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[MachineBooking]:
        """
        Get bookings for a specific machine within time range
        
        Args:
            machine_id: Machine ID
            start_time: Start time filter (milliseconds)
            end_time: End time filter (milliseconds)
            
        Returns:
            List of bookings for the machine
        """
        machine_bookings = [
            booking for booking in self.bookings.values()
            if booking.machine_id == machine_id
        ]
        
        # Apply time filters if provided
        if start_time is not None or end_time is not None:
            filtered_bookings = []
            for booking in machine_bookings:
                booking_end = booking.get_end_time()
                
                # Check if booking overlaps with time range
                if start_time is not None and booking_end <= start_time:
                    continue
                if end_time is not None and booking.start_time >= end_time:
                    continue
                    
                filtered_bookings.append(booking)
            machine_bookings = filtered_bookings
        
        return sorted(machine_bookings, key=lambda b: b.start_time)
    
    def update_booking(self, booking: MachineBooking) -> MachineBooking:
        """
        Update an existing booking
        
        Args:
            booking: Updated booking
            
        Returns:
            Updated booking
        """
        self.bookings[booking.booking_id] = booking
        self.save_database()
        
        event_system.publish("booking_updated", booking)
        return booking
    
    def delete_booking(self, booking_id: str) -> bool:
        """
        Delete a booking
        
        Args:
            booking_id: ID of booking to delete
            
        Returns:
            True if deleted successfully
        """
        if booking_id not in self.bookings:
            return False
        
        booking = self.bookings.pop(booking_id)
        self.save_database()
        
        event_system.publish("booking_deleted", booking_id)
        return True
    
    # Activity Type Management
    def get_activity_type(self, type_id: str) -> Optional[ActivityType]:
        """Get an activity type by ID"""
        return self.activity_types.get(type_id)
    
    def get_all_activity_types(self) -> Dict[str, ActivityType]:
        """Get all activity types"""
        return self.activity_types
    
    def create_activity_type(self, activity_type: ActivityType) -> ActivityType:
        """
        Create a new activity type
        
        Args:
            activity_type: ActivityType to create
            
        Returns:
            Created activity type
        """
        self.activity_types[activity_type.type_id] = activity_type
        self.save_activity_types()
        
        event_system.publish("activity_type_created", activity_type)
        return activity_type
    
    def update_activity_type(self, activity_type: ActivityType) -> ActivityType:
        """
        Update an existing activity type
        
        Args:
            activity_type: Updated activity type
            
        Returns:
            Updated activity type
        """
        self.activity_types[activity_type.type_id] = activity_type
        self.save_activity_types()
        
        event_system.publish("activity_type_updated", activity_type)
        return activity_type
    
    def delete_activity_type(self, type_id: str) -> bool:
        """
        Delete an activity type
        
        Args:
            type_id: ID of activity type to delete
            
        Returns:
            True if deleted successfully
        """
        if type_id not in self.activity_types:
            return False
        
        # Check if any bookings use this activity type
        bookings_using_type = [
            booking for booking in self.bookings.values()
            if booking.activity_type_id == type_id
        ]
        
        if bookings_using_type:
            event_system.publish("error", 
                f"Cannot delete activity type {type_id}: {len(bookings_using_type)} bookings are using it")
            return False
        
        activity_type = self.activity_types.pop(type_id)
        self.save_activity_types()
        
        event_system.publish("activity_type_deleted", type_id)
        return True
    
    # Conflict Detection and Resolution
    def find_booking_conflicts(self, booking: MachineBooking) -> List[MachineBooking]:
        """
        Find bookings that conflict with the given booking
        
        Args:
            booking: Booking to check for conflicts
            
        Returns:
            List of conflicting bookings
        """
        conflicts = []
        booking_end = booking.get_end_time()
        
        for other_booking in self.bookings.values():
            if other_booking.booking_id == booking.booking_id:
                continue
                
            if other_booking.machine_id != booking.machine_id:
                continue
                
            # Check for time overlap
            other_end = other_booking.get_end_time()
            if booking.start_time < other_end and booking_end > other_booking.start_time:
                conflicts.append(other_booking)
        
        return conflicts
    
    def resolve_booking_conflicts(
        self, 
        booking: MachineBooking, 
        scheduler_service
    ) -> List[Tuple[str, str]]:
        """
        Resolve conflicts by moving production jobs around bookings
        
        Args:
            booking: New booking causing conflicts
            scheduler_service: Scheduler service for moving parts
            
        Returns:
            List of (action, description) tuples describing resolutions
        """
        resolutions = []
        
        if not booking.conflicts_with_production():
            return resolutions
        
        # Get all parts on this machine that conflict with the booking
        all_parts = scheduler_service.get_all_parts()
        booking_end = booking.get_end_time()
        
        conflicting_parts = []
        for part in all_parts.values():
            if part.machine_id != booking.machine_id:
                continue
                
            job = scheduler_service.get_job(part.job_id)
            if not job:
                continue
                
            part_end = part.start_time + (job.cycle_time * 60 * 1000)
            
            # Check if part overlaps with booking
            if part.start_time < booking_end and part_end > booking.start_time:
                conflicting_parts.append((part, job))
        
        # Move conflicting parts to after the booking
        next_available_time = booking_end
        
        for part, job in sorted(conflicting_parts, key=lambda x: x[0].start_time):
            old_start = part.start_time
            scheduler_service.move_part(part.part_id, part.machine_id, next_available_time)
            
            resolutions.append((
                "moved_part",
                f"Moved {job.name} part {part.part_number} from {datetime.fromtimestamp(old_start/1000)} to {datetime.fromtimestamp(next_available_time/1000)}"
            ))
            
            next_available_time += (job.cycle_time * 60 * 1000)
        
        return resolutions
    
    def get_machine_availability(
        self, 
        machine_id: str, 
        start_time: int, 
        duration_minutes: int
    ) -> bool:
        """
        Check if machine is available for the given time period
        
        Args:
            machine_id: Machine ID
            start_time: Start time in milliseconds
            duration_minutes: Duration in minutes
            
        Returns:
            True if machine is available
        """
        end_time = start_time + (duration_minutes * 60 * 1000)
        machine_bookings = self.get_machine_bookings(machine_id, start_time, end_time)
        
        # Check for any blocking bookings in this time range
        for booking in machine_bookings:
            if booking.conflicts_with_production():
                return False
        
        return True
    
    def find_next_available_slot(
        self, 
        machine_id: str, 
        duration_minutes: int,
        start_search_time: Optional[int] = None
    ) -> Optional[int]:
        """
        Find the next available time slot for a booking
        
        Args:
            machine_id: Machine ID
            duration_minutes: Required duration in minutes
            start_search_time: When to start searching (default: now)
            
        Returns:
            Start time in milliseconds, or None if no slot found in next 30 days
        """
        if start_search_time is None:
            start_search_time = int(datetime.now().timestamp() * 1000)
        
        # Search for next 30 days
        search_end = start_search_time + (30 * 24 * 60 * 60 * 1000)
        
        # Get all bookings for this machine in search period
        bookings = self.get_machine_bookings(machine_id, start_search_time, search_end)
        blocking_bookings = [b for b in bookings if b.conflicts_with_production()]
        
        # Sort by start time
        blocking_bookings.sort(key=lambda b: b.start_time)
        
        # Check if we can start immediately
        current_time = start_search_time
        duration_ms = duration_minutes * 60 * 1000
        
        for booking in blocking_bookings:
            # Check if we have enough time before this booking
            if current_time + duration_ms <= booking.start_time:
                return current_time
            
            # Move search time to after this booking
            current_time = max(current_time, booking.get_end_time())
        
        # Check if we can fit after all bookings
        if current_time + duration_ms <= search_end:
            return current_time
        
        return None