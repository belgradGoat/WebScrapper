"""
Module Registry for NC Tool Analyzer
Provides a registry for discovering and managing modules
"""
import os
import sys
import importlib.util
import inspect
import logging
from typing import Dict, List, Any, Optional, Type

from .module_interface import ModuleInterface

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Registry for discovering and managing modules"""
    
    def __init__(self):
        """Initialize the module registry"""
        self.modules = {}
        self.module_paths = []
    
    def add_module_path(self, path: str) -> None:
        """
        Add a path to search for modules
        
        Args:
            path: Directory path to search for modules
        """
        if os.path.isdir(path) and path not in self.module_paths:
            self.module_paths.append(path)
    
    def discover_modules(self) -> None:
        """Scan module directories and load available modules"""
        for path in self.module_paths:
            self._discover_modules_in_path(path)
    
    def _discover_modules_in_path(self, path: str) -> None:
        """
        Discover modules in a specific path
        
        Args:
            path: Directory path to search for modules
        """
        logger.info(f"Discovering modules in {path}")
        
        # Walk through the directory
        for root, dirs, files in os.walk(path):
            # Look for Python files
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    module_path = os.path.join(root, file)
                    self._load_module_from_file(module_path)
    
    def _load_module_from_file(self, module_path: str) -> None:
        """
        Load a module from a file
        
        Args:
            module_path: Path to the module file
        """
        try:
            # Generate a unique module name
            module_name = f"dynamic_module_{hash(module_path)}"
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None:
                logger.warning(f"Could not load module spec from {module_path}")
                return
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find module classes
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, ModuleInterface) and 
                    obj != ModuleInterface):
                    
                    # Create an instance of the module
                    try:
                        module_instance = obj()
                        module_name = module_instance.get_name()
                        
                        # Register the module
                        self.modules[module_name] = module_instance
                        logger.info(f"Registered module: {module_name}")
                    except Exception as e:
                        logger.error(f"Error instantiating module class {name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error loading module from {module_path}: {str(e)}")
    
    def get_module(self, name: str) -> Optional[ModuleInterface]:
        """
        Get a module by name
        
        Args:
            name: Name of the module
            
        Returns:
            Module instance or None if not found
        """
        return self.modules.get(name)
    
    def get_all_modules(self) -> Dict[str, ModuleInterface]:
        """
        Get all registered modules
        
        Returns:
            Dictionary of all registered modules
        """
        return self.modules.copy()
    
    def get_modules_by_type(self, module_type: Type) -> List[ModuleInterface]:
        """
        Get modules of a specific type
        
        Args:
            module_type: Type of modules to get
            
        Returns:
            List of modules of the specified type
        """
        return [m for m in self.modules.values() if isinstance(m, module_type)]
    
    def initialize_modules(self, service_registry) -> None:
        """
        Initialize all modules with required services
        
        Args:
            service_registry: ServiceRegistry instance
        """
        # Sort modules by dependencies
        modules_order = self._resolve_module_dependencies()
        
        # Initialize modules in order
        for module_name in modules_order:
            module = self.modules[module_name]
            try:
                logger.info(f"Initializing module: {module_name}")
                module.initialize(service_registry)
                
                # If it's a service module, register its services
                if hasattr(module, 'get_provided_services'):
                    services = module.get_provided_services()
                    for service_name, service in services.items():
                        service_registry.register_service(service_name, service)
                        logger.info(f"Registered service: {service_name} from module {module_name}")
            
            except Exception as e:
                logger.error(f"Error initializing module {module_name}: {str(e)}")
    
    def _resolve_module_dependencies(self) -> List[str]:
        """
        Sort modules by dependencies
        
        Returns:
            List of module names in dependency order
        """
        # Create a graph of module dependencies
        graph = {}
        for module_name, module in self.modules.items():
            required_services = set(module.get_required_services())
            graph[module_name] = required_services
        
        # Topological sort
        result = []
        visited = set()
        temp_visited = set()
        
        def visit(node):
            if node in temp_visited:
                logger.warning(f"Circular dependency detected: {node}")
                return
            if node in visited:
                return
            
            temp_visited.add(node)
            
            # Find modules that provide the required services
            for service in graph.get(node, []):
                for module_name, module in self.modules.items():
                    if hasattr(module, 'get_provided_services'):
                        if service in module.get_provided_services():
                            visit(module_name)
            
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        # Visit all nodes
        for module_name in graph:
            if module_name not in visited:
                visit(module_name)
        
        return result
    
    def shutdown_modules(self) -> None:
        """Shutdown all modules"""
        for module_name, module in self.modules.items():
            try:
                logger.info(f"Shutting down module: {module_name}")
                module.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down module {module_name}: {str(e)}")