"""
JMS Service Module for NC Tool Analyzer
Provides the JMS service as a module
"""
import logging
import tkinter.messagebox as messagebox
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
    JMS_AVAILABLE = True  # Module is available even if requests is not
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
        self.username = None
        self.password = None
        self.client_id = "EsbusciClient"
        self.client_secret = "DefaultEsbusciClientSecret"
        self.base_url = "http://localhost:8080"  # Default URL
        self.config_manager = None
    
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
            
            # Get the config manager
            logger.info("Looking for config_manager in service registry")
            self.config_manager = service_registry.get_service("config_manager")
            if not self.config_manager:
                logger.warning("Config manager not found in service registry, using default values")
            else:
                logger.info("Found config_manager, loading JMS configuration")
                self._load_config()
            
            # Create the JMS service (disabled by default)
            logger.info("Creating JMS service instance")
            self.jms_service = JMSService(
                scheduler_service,
                base_url=self.base_url,
                username=self.username,
                password=self.password,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
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
    
    def _load_config(self) -> None:
        """Load JMS configuration from config manager"""
        if not self.config_manager:
            logger.warning("Config manager not available, cannot load JMS configuration")
            return
            
        try:
            # Get JMS module configuration
            jms_config = self.config_manager.get_module_config("jms_service_module")
            
            logger.info(f"=== LOADING JMS CONFIG FROM CONFIG MANAGER ===")
            logger.info(f"Raw JMS config: {jms_config}")
            
            # Update values from config
            old_base_url = self.base_url
            self.base_url = jms_config.get("base_url", self.base_url)
            self.username = jms_config.get("username", self.username)
            self.password = jms_config.get("password", self.password)
            self.client_id = jms_config.get("client_id", self.client_id)
            self.client_secret = jms_config.get("client_secret", self.client_secret)
            self.jms_enabled = jms_config.get("enabled", self.jms_enabled)
            
            logger.info(f"Base URL changed from '{old_base_url}' to '{self.base_url}'")
            logger.info(f"JMS enabled: {self.jms_enabled}")
            logger.info(f"Username provided: {self.username is not None}")
            logger.info(f"=== JMS CONFIG LOADING COMPLETE ===")
            
        except Exception as e:
            logger.error(f"Failed to load JMS configuration: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _save_config(self) -> None:
        """Save JMS configuration to config manager"""
        if not self.config_manager:
            logger.warning("Config manager not available, cannot save JMS configuration")
            return
            
        # Get JMS module configuration
        jms_config = self.config_manager.get_module_config("jms_service_module")
        
        # Update values
        jms_config["base_url"] = self.base_url
        jms_config["username"] = self.username
        jms_config["password"] = self.password
        jms_config["client_id"] = self.client_id
        jms_config["client_secret"] = self.client_secret
        jms_config["enabled"] = self.jms_enabled
        
        # Save configuration
        self.config_manager.save_config()
        logger.info(f"Saved JMS configuration: URL={self.base_url}, Username={self.username is not None}")
    
    def enable_jms(self, base_url: str = None, username: str = None, password: str = None) -> bool:
        """
        Enable JMS integration
        
        Args:
            base_url: Base URL of the JMS API
            username: Username for authentication (optional)
            password: Password for authentication (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not JMS_AVAILABLE or not self.jms_service:
            logger.error("JMS service not available")
            return False
            
        if not self.jms_enabled:
            try:
                logger.info(f"=== ENABLING JMS INTEGRATION ===")
                logger.info(f"Provided base_url parameter: {base_url}")
                logger.info(f"Current self.base_url: {self.base_url}")
                
                # Use provided values or current values
                base_url = base_url or self.base_url
                
                logger.info(f"Final base_url to use: {base_url}")
                logger.info(f"Enabling JMS integration with URL: {base_url}")
                if username and password:
                    logger.info("Using username/password authentication")
                    self.username = username
                    self.password = password
                
                # Update base URL
                old_base_url = self.base_url
                self.base_url = base_url
                logger.info(f"Updated self.base_url from '{old_base_url}' to '{self.base_url}'")
                
                # Create new JMS service with provided URL and credentials
                scheduler_service = self.jms_service.scheduler_service
                logger.info(f"Creating new JMSService with base_url: {base_url}")
                self.jms_service = JMSService(
                    scheduler_service,
                    base_url,
                    username=self.username,
                    password=self.password,
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                
                # Test connection
                logger.info("Testing JMS connection")
                connection_result = self.jms_service.test_connection()
                logger.info(f"Connection test result: {connection_result}")
                
                if connection_result:
                    # Start polling
                    logger.info("Starting JMS polling")
                    self.jms_service.start_polling()
                    self.jms_enabled = True
                    
                    # Save configuration
                    self._save_config()
                    
                    # Publish event
                    event_system.publish("jms_enabled", f"JMS integration enabled with URL: {base_url}")
                    logger.info("JMS integration enabled successfully")
                    
                    return True
                else:
                    logger.warning(f"Failed to connect to JMS API at {base_url}")
                    # If requests is not available, enable anyway with mock functionality
                    if not REQUESTS_AVAILABLE:
                        logger.info("Using mock JMS functionality")
                        self.jms_enabled = True
                        
                        # Save configuration
                        self._save_config()
                        
                        event_system.publish("jms_enabled", f"JMS integration enabled with mock functionality")
                        return True
                    
                    # Ask user if they want to enable anyway
                    try:
                        if messagebox.askyesno("Connection Failed",
                                              "Failed to connect to JMS API. Enable integration anyway?"):
                            logger.info("Enabling JMS integration despite connection failure")
                            self.jms_enabled = True
                            
                            # Save configuration
                            self._save_config()
                            
                            event_system.publish("jms_enabled", f"JMS integration enabled with URL: {base_url} (connection failed)")
                            return True
                    except Exception as e:
                        logger.error(f"Error showing messagebox: {str(e)}")
                        # If messagebox fails, enable anyway as a fallback
                        logger.info("Enabling JMS integration despite connection failure (fallback)")
                        self.jms_enabled = True
                        
                        # Save configuration
                        self._save_config()
                        
                        event_system.publish("jms_enabled", f"JMS integration enabled with URL: {base_url} (connection failed)")
                        return True
                        
                    return False
            except Exception as e:
                logger.error(f"Error enabling JMS integration: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
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
                
                # Save configuration
                self._save_config()
                
                # Publish event
                event_system.publish("jms_disabled", "JMS integration disabled")
            except Exception as e:
                logger.error(f"Error disabling JMS integration: {str(e)}")
    
    def shutdown(self) -> None:
        """Shutdown the module and release resources"""
        logger.info("Shutting down JMS service module")
        self.disable_jms()
        
    def get_base_url(self) -> str:
        """Get the base URL for JMS API"""
        return self.base_url
        
    def get_username(self) -> str:
        """Get the username for JMS authentication"""
        return self.username
        
    def get_password(self) -> str:
        """Get the password for JMS authentication"""
        return self.password