#!/usr/bin/env python3
"""
Test script to verify JMS module loading
"""
import os
import sys
import logging
import importlib.util

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_jms_modules")

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    logger.info(f"Added current directory to path: {current_dir}")

# Print Python path
logger.info(f"Python path: {sys.path}")

def test_imports():
    """Test importing JMS modules directly"""
    logger.info("Testing direct imports...")
    
    # Test importing JMS service
    try:
        logger.info("Trying to import JMSService...")
        from services.jms_service import JMSService
        logger.info("Successfully imported JMSService")
    except ImportError as e:
        logger.error(f"Failed to import JMSService: {str(e)}")
    
    # Test importing JMS auth
    try:
        logger.info("Trying to import JMS auth...")
        from services.jms.jms_auth import REQUESTS_AVAILABLE
        logger.info(f"Successfully imported JMS auth, REQUESTS_AVAILABLE={REQUESTS_AVAILABLE}")
    except ImportError as e:
        logger.error(f"Failed to import JMS auth: {str(e)}")
    
    # Test importing JMS config dialog
    try:
        logger.info("Trying to import JMSConfigDialog...")
        from ui.jms_config_dialog import JMSConfigDialog
        logger.info("Successfully imported JMSConfigDialog")
    except ImportError as e:
        logger.error(f"Failed to import JMSConfigDialog: {str(e)}")

def test_module_loading():
    """Test loading JMS modules through the module system"""
    logger.info("Testing module loading...")
    
    # Import module system components
    try:
        logger.info("Importing module system components...")
        from module_system.service_registry import ServiceRegistry
        from module_system.module_registry import ModuleRegistry
        logger.info("Successfully imported module system components")
        
        # Create registries
        service_registry = ServiceRegistry()
        module_registry = ModuleRegistry()
        
        # Add module paths
        core_modules_path = os.path.join(current_dir, "core_modules")
        if os.path.isdir(core_modules_path):
            logger.info(f"Adding module path: {core_modules_path}")
            module_registry.add_module_path(core_modules_path)
        else:
            logger.error(f"Core modules path not found: {core_modules_path}")
        
        # Discover modules
        logger.info("Discovering modules...")
        module_registry.discover_modules()
        
        # Check if JMS modules were found
        modules = module_registry.get_all_modules()
        logger.info(f"Found {len(modules)} modules:")
        for name, module in modules.items():
            logger.info(f"  - {name} (v{module.get_version()})")
        
        # Check specifically for JMS modules
        jms_service_module = module_registry.get_module("jms_service_module")
        if jms_service_module:
            logger.info("JMS service module found")
        else:
            logger.error("JMS service module not found")
        
        jms_menu_module = module_registry.get_module("jms_menu_extension_module")
        if jms_menu_module:
            logger.info("JMS menu extension module found")
        else:
            logger.error("JMS menu extension module not found")
        
        # Initialize modules
        logger.info("Initializing modules...")
        module_registry.initialize_modules(service_registry)
        
        # Check if JMS service was registered
        jms_service = service_registry.get_service("jms_service")
        if jms_service:
            logger.info("JMS service registered successfully")
        else:
            logger.error("JMS service not registered")
            
        # Check if JMS service module was registered
        jms_service_module = service_registry.get_service("jms_service_module")
        if jms_service_module:
            logger.info("JMS service module registered successfully")
        else:
            logger.error("JMS service module not registered")
        
    except Exception as e:
        logger.error(f"Error testing module loading: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    logger.info("Starting JMS module tests")
    
    # Test direct imports
    test_imports()
    
    # Test module loading
    test_module_loading()
    
    logger.info("JMS module tests completed")