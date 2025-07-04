"""
Event System for NC Tool Analyzer
Provides a simple event system for communication between components
"""

class EventSystem:
    """
    Simple event system for communication between components
    """
    def __init__(self):
        self.listeners = {}
        
    def subscribe(self, event_name, callback):
        """
        Subscribe to an event
        
        Args:
            event_name (str): Name of the event to subscribe to
            callback (callable): Function to call when event is triggered
        """
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
        
    def unsubscribe(self, event_name, callback):
        """
        Unsubscribe from an event
        
        Args:
            event_name (str): Name of the event to unsubscribe from
            callback (callable): Function to remove from event listeners
        """
        if event_name in self.listeners and callback in self.listeners[event_name]:
            self.listeners[event_name].remove(callback)
            
    def publish(self, event_name, *args, **kwargs):
        """
        Publish an event to all subscribers
        
        Args:
            event_name (str): Name of the event to publish
            *args, **kwargs: Arguments to pass to the callback functions
        """
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback(*args, **kwargs)

# Global event system instance
event_system = EventSystem()