"""
Extension Registry for NC Tool Analyzer
Provides a system for registering and invoking extension points
"""
from typing import Dict, List, Any, Callable
import logging

logger = logging.getLogger(__name__)


class ExtensionPoint:
    """
    Represents an extension point where modules can register handlers
    """
    def __init__(self, name: str):
        """
        Initialize the extension point
        
        Args:
            name: Name of the extension point
        """
        self.name = name
        self.handlers = []
    
    def register_handler(self, handler: Callable) -> None:
        """
        Register a handler for this extension point
        
        Args:
            handler: Function to call when the extension point is invoked
        """
        if handler not in self.handlers:
            self.handlers.append(handler)
            logger.debug(f"Registered handler for extension point {self.name}")
    
    def unregister_handler(self, handler: Callable) -> None:
        """
        Unregister a handler from this extension point
        
        Args:
            handler: Function to remove from handlers
        """
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.debug(f"Unregistered handler for extension point {self.name}")
    
    def invoke(self, *args, **kwargs) -> List[Any]:
        """
        Invoke all handlers for this extension point
        
        Args:
            *args, **kwargs: Arguments to pass to handlers
            
        Returns:
            List of results from all handlers
        """
        results = []
        for handler in self.handlers:
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error invoking handler for extension point {self.name}: {str(e)}")
        return results


class ExtensionRegistry:
    """
    Registry for extension points
    """
    def __init__(self):
        """Initialize the extension registry"""
        self.extension_points = {}
    
    def register_extension_point(self, name: str) -> ExtensionPoint:
        """
        Register an extension point
        
        Args:
            name: Name of the extension point
            
        Returns:
            ExtensionPoint instance
        """
        if name not in self.extension_points:
            self.extension_points[name] = ExtensionPoint(name)
            logger.info(f"Registered extension point: {name}")
        return self.extension_points[name]
    
    def get_extension_point(self, name: str) -> ExtensionPoint:
        """
        Get an extension point by name
        
        Args:
            name: Name of the extension point
            
        Returns:
            ExtensionPoint instance
        """
        if name not in self.extension_points:
            self.register_extension_point(name)
        return self.extension_points[name]
    
    def has_extension_point(self, name: str) -> bool:
        """
        Check if an extension point exists
        
        Args:
            name: Name of the extension point
            
        Returns:
            True if the extension point exists, False otherwise
        """
        return name in self.extension_points