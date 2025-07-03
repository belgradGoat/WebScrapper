"""
JMS Service Module for NC Tool Analyzer
Provides the JMS service as a module
"""
import logging
from typing import Dict, List, Any

from module_system.module_interface import ServiceModuleInterface
from utils.event_system import event_system

logger = logging.getLogger(__name__)

# Try to import JMS modules
try:
    logger.info("Attempting to import JMS modules...")
    # Try absolute imports first
    try:
        from services.jms_service import JMSService
        from services.jms.jms_auth import REQUESTS_AVAILABLE
        logger.info("Successfully imported JMS modules using absolute imports")
    except ImportError:
        # Try relative imports
        logger.info("Absolute imports failed, trying relative imports...")
        import sys
        import os
        # Add parent directory to path to enable relative imports
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
            logger.info(f"Added parent directory to path: {parent_dir}")
        
        from services.jms_service import JMSService
        from services.jms.jms_auth import REQUESTS_AVAILABLE
        logger.info("Successfully imported JMS modules using relative imports")
    
    logger.info(f"JMS auth module imported, REQUESTS_AVAILABLE={REQUESTS_AVAILABLE}")
    JMS_AVAILABLE = REQUESTS_AVAILABLE
except ImportError as e:
    JMS_AVAILABLE = False
    logger.error(f"JMS modules import error: {str(e)}")
    logger.error(f"Python path: {sys.path}")
    logger.warning("JMS modules not found. JMS integration will not be available.")


class JMSServiceModule(ServiceModuleInterface):
    """Module that provides the JMS service"""
    
    def __init__(self):
        """Initialize the module"""
        self.jms_service = None
        self.jms_enabled = False
    
    def get_name(self) -> str:
        """Return the name of the module"""
        return "jms_service_module"
    
    def get_version(self) -> str:
        """Return the version of the module"""
        return "1.0.0"
    
    def get_description(self) -> str:
        """Return a description of the module"""
        return "Provides the JMS service for integration with Job Management System"
    
    def get_required_services(self) -> List[str]:
        """Return list of service names this module requires"""
        return ["scheduler_service"]
    
    def initialize(self, service_registry) -> None:
        """Initialize the module with required services"""
        logger.info("Initializing JMS service module")
        
        if not JMS_AVAILABLE:
            logger.warning("JMS service not available. Skipping initialization.")
            event_system.publish("error", "JMS modules not found. JMS integration will not be available.")
            return
        
        try:
            # Get the scheduler service
            logger.info("Looking for scheduler_service in service registry")
            scheduler_service = service_registry.get_service("scheduler_service")
            if not scheduler_service:
                logger.error("Scheduler service not found in service registry")
                raise ValueError("Scheduler service not found")
            else:
                logger.info(f"Found scheduler_service: {type(scheduler_service).__name__}")
            
            # Create the JMS service (disabled by default)
            logger.info("Creating JMS service instance")
            self.jms_service = JMSService(scheduler_service)
            logger.info("JMS service created successfully")
            
        except Exception as e:
            logger.error(f"Error initializing JMS service: {str(e)}")
            logger.error(f"Exception details: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            event_system.publish("error", f"Error initializing JMS service: {str(e)}")
    
    def get_provided_services(self) -> Dict[str, Any]:
        """Return a dictionary of services provided by this module"""
        if self.jms_service:
            logger.info("Providing jms_service to service registry")
            return {
                "jms_service": self.jms_service
            }
        logger.warning("No JMS service available to provide")
        return {}
    
    def enable_jms(self, base_url: str = "http://localhost:8080") -> bool:
        """
        Enable JMS integration
        
        Args:
            base_url: Base URL of the JMS API
            
        Returns:
            True if successful, False otherwise
        """
        if not JMS_AVAILABLE or not self.jms_service:
            logger.error("JMS service not available")
            return False
            
        if not self.jms_enabled:
            try:
                # Create new JMS service with provided URL
                scheduler_service = self.jms_service.scheduler_service
                self.jms_service = JMSService(scheduler_service, base_url)
                
                # Test connection
                if self.jms_service.test_connection():
                    # Start polling
                    self.jms_service.start_polling()
                    self.jms_enabled = True
                    
                    # Publish event
                    event_system.publish("jms_enabled", f"JMS integration enabled with URL: {base_url}")
                    
                    return True
                else:
                    logger.error(f"Failed to connect to JMS API at {base_url}")
                    return False
            except Exception as e:
                logger.error(f"Error enabling JMS integration: {str(e)}")
                return False
        return True
    
    def disable_jms(self) -> None:
        """Disable JMS integration"""
        if not JMS_AVAILABLE or not self.jms_service:
            return
            
        if self.jms_enabled:
            try:
                # Stop polling
                self.jms_service.stop_polling()
                self.jms_enabled = False
                
                # Publish event
                event_system.publish("jms_disabled", "JMS integration disabled")
            except Exception as e:
                logger.error(f"Error disabling JMS integration: {str(e)}")
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down JMS service module")
        self.disable_jms()