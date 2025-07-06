#!/usr/bin/env python3
"""
Debug script to check module discovery and registration
"""

import logging
import sys
from application_core import ApplicationCore

# Set up logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def debug_modules():
    """Debug module discovery"""
    try:
        logger.info("Creating ApplicationCore...")
        app_core = ApplicationCore()
        
        logger.info("Module paths registered:")
        for path in app_core.module_registry.module_paths:
            logger.info(f"  - {path}")
        
        logger.info("Initializing ApplicationCore...")
        success = app_core.initialize()
        
        if not success:
            logger.error("Failed to initialize ApplicationCore")
            return
        
        logger.info("ApplicationCore initialized successfully")
        
        # Check discovered modules
        modules = app_core.module_registry.get_all_modules()
        logger.info(f"Discovered {len(modules)} modules:")
        for name, module in modules.items():
            logger.info(f"  - {name} (v{module.get_version()}): {module.get_description()}")
            if hasattr(module, 'get_provided_services'):
                services = module.get_provided_services()
                if services:
                    logger.info(f"    Provides services: {list(services.keys())}")
            logger.info(f"    Requires services: {module.get_required_services()}")
        
        # Check available services
        services = []
        for service_name in ['machine_service', 'analysis_service', 'scheduler_service', 'jms_service']:
            service = app_core.service_registry.get_service(service_name)
            if service:
                services.append(f"{service_name}: {type(service).__name__}")
            else:
                services.append(f"{service_name}: NOT FOUND")
        
        logger.info("Available services:")
        for service in services:
            logger.info(f"  - {service}")
        
        # Check tab modules specifically
        from module_system.module_interface import TabModuleInterface
        tab_modules = app_core.module_registry.get_modules_by_type(TabModuleInterface)
        logger.info(f"Found {len(tab_modules)} tab modules:")
        for tab_module in tab_modules:
            logger.info(f"  - {tab_module.get_name()}: {tab_module.get_tab_name()}")
        
        app_core.shutdown()
        
    except Exception as e:
        logger.error(f"Error during debug: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_modules()