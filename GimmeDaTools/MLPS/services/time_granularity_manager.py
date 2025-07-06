"""
Time Granularity Manager for configurable schedule display
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional, Literal
import math


class TimeGranularityManager:
    """
    Manages time granularity settings and calculations for the scheduler
    """
    
    # Available granularities in minutes
    GRANULARITIES = {
        '5min': 5,
        '15min': 15,
        '30min': 30,
        '1hr': 60
    }
    
    # Base pixel width per hour (will be scaled by granularity)
    BASE_PIXELS_PER_HOUR = 60
    
    def __init__(self, default_granularity: str = '1hr'):
        """
        Initialize the time granularity manager
        
        Args:
            default_granularity: Default granularity setting
        """
        self.current_granularity = default_granularity
        self.validate_granularity(self.current_granularity)
        
    def validate_granularity(self, granularity: str) -> bool:
        """
        Validate that granularity is supported
        
        Args:
            granularity: Granularity string to validate
            
        Returns:
            True if valid
            
        Raises:
            ValueError: If granularity is not supported
        """
        if granularity not in self.GRANULARITIES:
            raise ValueError(f"Unsupported granularity: {granularity}. Supported: {list(self.GRANULARITIES.keys())}")
        return True
    
    def set_granularity(self, granularity: str) -> None:
        """
        Set the current granularity
        
        Args:
            granularity: New granularity setting
        """
        self.validate_granularity(granularity)
        self.current_granularity = granularity
    
    def get_granularity(self) -> str:
        """Get the current granularity setting"""
        return self.current_granularity
    
    def get_granularity_minutes(self, granularity: Optional[str] = None) -> int:
        """
        Get granularity in minutes
        
        Args:
            granularity: Granularity to check (uses current if None)
            
        Returns:
            Granularity in minutes
        """
        gran = granularity or self.current_granularity
        return self.GRANULARITIES[gran]
    
    def get_pixels_per_granularity_unit(self, granularity: Optional[str] = None) -> float:
        """
        Calculate pixels per granularity unit
        
        Args:
            granularity: Granularity to calculate for (uses current if None)
            
        Returns:
            Pixels per granularity unit
        """
        gran = granularity or self.current_granularity
        minutes_per_unit = self.get_granularity_minutes(gran)
        
        # Scale base pixels per hour based on granularity
        pixels_per_hour = self.BASE_PIXELS_PER_HOUR
        pixels_per_minute = pixels_per_hour / 60
        
        return pixels_per_minute * minutes_per_unit
    
    def calculate_pixel_width(
        self, 
        duration_minutes: int, 
        granularity: Optional[str] = None
    ) -> int:
        """
        Calculate pixel width for a given duration
        
        Args:
            duration_minutes: Duration in minutes
            granularity: Granularity to use (uses current if None)
            
        Returns:
            Width in pixels
        """
        gran = granularity or self.current_granularity
        pixels_per_minute = self.get_pixels_per_granularity_unit(gran) / self.get_granularity_minutes(gran)
        
        return max(1, int(duration_minutes * pixels_per_minute))
    
    def calculate_pixel_offset(
        self, 
        time_offset_minutes: float, 
        granularity: Optional[str] = None
    ) -> int:
        """
        Calculate pixel offset for a time offset
        
        Args:
            time_offset_minutes: Time offset in minutes from reference point
            granularity: Granularity to use (uses current if None)
            
        Returns:
            Pixel offset
        """
        gran = granularity or self.current_granularity
        pixels_per_minute = self.get_pixels_per_granularity_unit(gran) / self.get_granularity_minutes(gran)
        
        return int(time_offset_minutes * pixels_per_minute)
    
    def get_time_slots(
        self, 
        day_start: datetime, 
        granularity: Optional[str] = None
    ) -> List[datetime]:
        """
        Get time slots for a day based on granularity
        
        Args:
            day_start: Start of the day
            granularity: Granularity to use (uses current if None)
            
        Returns:
            List of time slot start times
        """
        gran = granularity or self.current_granularity
        slot_minutes = self.get_granularity_minutes(gran)
        
        slots = []
        current_time = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = current_time + timedelta(days=1)
        
        while current_time < day_end:
            slots.append(current_time)
            current_time += timedelta(minutes=slot_minutes)
        
        return slots
    
    def snap_to_grid(
        self, 
        timestamp: int, 
        granularity: Optional[str] = None,
        snap_direction: Literal['floor', 'ceil', 'round'] = 'round'
    ) -> int:
        """
        Snap a timestamp to the nearest granularity boundary
        
        Args:
            timestamp: Timestamp in milliseconds
            granularity: Granularity to use (uses current if None)
            snap_direction: Direction to snap (floor, ceil, or round)
            
        Returns:
            Snapped timestamp in milliseconds
        """
        gran = granularity or self.current_granularity
        slot_minutes = self.get_granularity_minutes(gran)
        slot_ms = slot_minutes * 60 * 1000
        
        # Convert to datetime for easier manipulation
        dt = datetime.fromtimestamp(timestamp / 1000)
        
        # Get start of day
        day_start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start_ms = int(day_start.timestamp() * 1000)
        
        # Calculate offset from day start
        offset_ms = timestamp - day_start_ms
        
        # Snap to granularity boundary
        if snap_direction == 'floor':
            snapped_offset = (offset_ms // slot_ms) * slot_ms
        elif snap_direction == 'ceil':
            snapped_offset = math.ceil(offset_ms / slot_ms) * slot_ms
        else:  # round
            snapped_offset = round(offset_ms / slot_ms) * slot_ms
        
        return day_start_ms + snapped_offset
    
    def get_time_range_for_view(
        self, 
        center_time: datetime, 
        view_width_hours: int = 24
    ) -> Tuple[datetime, datetime]:
        """
        Get the time range that should be displayed in the view
        
        Args:
            center_time: Center time for the view
            view_width_hours: Width of view in hours
            
        Returns:
            Tuple of (start_time, end_time)
        """
        half_width = timedelta(hours=view_width_hours / 2)
        start_time = center_time - half_width
        end_time = center_time + half_width
        
        return start_time, end_time
    
    def calculate_zoom_level(self, granularity: str) -> float:
        """
        Calculate zoom level based on granularity
        
        Args:
            granularity: Granularity to calculate zoom for
            
        Returns:
            Zoom level (1.0 = normal, >1.0 = zoomed in)
        """
        base_minutes = self.GRANULARITIES['1hr']  # Use 1hr as base
        current_minutes = self.GRANULARITIES[granularity]
        
        # Smaller granularity = higher zoom level
        return base_minutes / current_minutes
    
    def get_optimal_granularity_for_duration(self, duration_minutes: int) -> str:
        """
        Get the optimal granularity for displaying a given duration
        
        Args:
            duration_minutes: Duration in minutes
            
        Returns:
            Optimal granularity string
        """
        # Rules for optimal granularity:
        # - Very short durations (< 30 min) -> 5min
        # - Short durations (30-90 min) -> 15min  
        # - Medium durations (90-240 min) -> 30min
        # - Long durations (> 240 min) -> 1hr
        
        if duration_minutes < 30:
            return '5min'
        elif duration_minutes < 90:
            return '15min'
        elif duration_minutes < 240:
            return '30min'
        else:
            return '1hr'
    
    def format_time_slot_label(
        self, 
        slot_time: datetime, 
        granularity: Optional[str] = None
    ) -> str:
        """
        Format a time slot label for display
        
        Args:
            slot_time: Time slot datetime
            granularity: Granularity to use (uses current if None)
            
        Returns:
            Formatted time label
        """
        gran = granularity or self.current_granularity
        
        if gran == '5min':
            return slot_time.strftime("%H:%M")
        elif gran == '15min':
            return slot_time.strftime("%H:%M")
        elif gran == '30min':
            if slot_time.minute == 0:
                return slot_time.strftime("%H:00")
            else:
                return slot_time.strftime("%H:30")
        else:  # 1hr
            return slot_time.strftime("%H:00")
    
    def get_visible_time_labels(
        self, 
        day_start: datetime, 
        granularity: Optional[str] = None
    ) -> List[Tuple[datetime, str, int]]:
        """
        Get time labels that should be visible for a day
        
        Args:
            day_start: Start of the day
            granularity: Granularity to use (uses current if None)
            
        Returns:
            List of (datetime, label, pixel_position) tuples
        """
        gran = granularity or self.current_granularity
        time_slots = self.get_time_slots(day_start, gran)
        
        labels = []
        for i, slot_time in enumerate(time_slots):
            label = self.format_time_slot_label(slot_time, gran)
            pixel_position = i * self.get_pixels_per_granularity_unit(gran)
            labels.append((slot_time, label, int(pixel_position)))
        
        return labels
    
    def calculate_day_width_pixels(self, granularity: Optional[str] = None) -> int:
        """
        Calculate the total pixel width needed for one day
        
        Args:
            granularity: Granularity to use (uses current if None)
            
        Returns:
            Day width in pixels
        """
        gran = granularity or self.current_granularity
        slots_per_day = 24 * 60 // self.get_granularity_minutes(gran)
        pixels_per_slot = self.get_pixels_per_granularity_unit(gran)
        
        return int(slots_per_day * pixels_per_slot)
    
    def get_granularity_info(self, granularity: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive information about a granularity setting
        
        Args:
            granularity: Granularity to get info for (uses current if None)
            
        Returns:
            Dictionary with granularity information
        """
        gran = granularity or self.current_granularity
        
        return {
            'granularity': gran,
            'minutes_per_unit': self.get_granularity_minutes(gran),
            'pixels_per_unit': self.get_pixels_per_granularity_unit(gran),
            'slots_per_hour': 60 // self.get_granularity_minutes(gran),
            'slots_per_day': 24 * 60 // self.get_granularity_minutes(gran),
            'day_width_pixels': self.calculate_day_width_pixels(gran),
            'zoom_level': self.calculate_zoom_level(gran),
            'display_name': self._get_granularity_display_name(gran)
        }
    
    def _get_granularity_display_name(self, granularity: str) -> str:
        """Get user-friendly display name for granularity"""
        display_names = {
            '5min': '5 Minutes',
            '15min': '15 Minutes', 
            '30min': '30 Minutes',
            '1hr': '1 Hour'
        }
        return display_names.get(granularity, granularity)
    
    def get_all_granularities_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available granularities
        
        Returns:
            Dictionary mapping granularity to info
        """
        return {
            gran: self.get_granularity_info(gran) 
            for gran in self.GRANULARITIES.keys()
        }
    
    def convert_minutes_to_pixels(
        self, 
        minutes: float, 
        granularity: Optional[str] = None
    ) -> int:
        """
        Convert minutes to pixels for the current granularity
        
        Args:
            minutes: Duration in minutes
            granularity: Granularity to use (uses current if None)
            
        Returns:
            Equivalent pixels
        """
        return self.calculate_pixel_width(int(minutes), granularity)
    
    def convert_pixels_to_minutes(
        self, 
        pixels: int, 
        granularity: Optional[str] = None
    ) -> float:
        """
        Convert pixels to minutes for the current granularity
        
        Args:
            pixels: Width in pixels
            granularity: Granularity to use (uses current if None)
            
        Returns:
            Equivalent minutes
        """
        gran = granularity or self.current_granularity
        pixels_per_minute = self.get_pixels_per_granularity_unit(gran) / self.get_granularity_minutes(gran)
        
        return pixels / pixels_per_minute if pixels_per_minute > 0 else 0