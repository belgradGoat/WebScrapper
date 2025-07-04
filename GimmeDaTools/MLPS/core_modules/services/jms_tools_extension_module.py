"""
JMS Tools Extension Module
Adds JMS tools to the application menu
"""
import logging
from module_system.module_interface import ModuleInterface
from utils.event_system import event_system

# Set up logger
logger = logging.getLogger(__name__)

class JMSToolsExtensionModule(ModuleInterface):
    """Module that adds JMS tools to the application menu"""
    
    def __init__(self):
        """Initialize the module"""
        super().__init__()
        self.name = "JMS Tools Extension"
        self.version = "1.0.0"
        self.description = "Adds JMS tools to the application menu"
        self.author = "MLPS Team"
        
        # Dependencies
        self.dependencies = ["jms_service_module"]
        
        # Reference to the JMS service
        self.jms_service = None
        
        # Menu items
        self.menu_items = []
    
    def initialize(self) -> bool:
        """
        Initialize the module
        
        Returns:
            True if initialization was successful, False otherwise
        """
        logger.info("Initializing JMS Tools Extension Module")
        
        try:
            # Get JMS service
            self.jms_service = self.service_registry.get_service("jms_service")
            if not self.jms_service:
                logger.error("JMS service not found")
                return False
            
            # Register menu items
            self._register_menu_items()
            
            logger.info("JMS Tools Extension Module initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize JMS Tools Extension Module: {str(e)}")
            return False
    
    def shutdown(self) -> None:
        """Shutdown the module"""
        logger.info("Shutting down JMS Tools Extension Module")
        
        # Unregister menu items
        for menu_item in self.menu_items:
            event_system.unsubscribe("menu_item_clicked", menu_item)
    
    def _register_menu_items(self) -> None:
        """Register menu items"""
        # JMS Tools menu item
        jms_tools_id = "jms_tools"
        event_system.subscribe("menu_item_clicked", jms_tools_id, self._on_jms_tools_clicked)
        self.menu_items.append(jms_tools_id)
        
        # Register menu item with the extension registry
        self.extension_registry.register_menu_item(
            "tools",  # Parent menu
            {
                "id": jms_tools_id,
                "label": "JMS Tools",
                "tooltip": "Access JMS tools and utilities",
                "enabled": True
            }
        )
        
        # JMS Cell Monitor menu item
        cell_monitor_id = "jms_cell_monitor"
        event_system.subscribe("menu_item_clicked", cell_monitor_id, self._on_cell_monitor_clicked)
        self.menu_items.append(cell_monitor_id)
        
        # Register menu item with the extension registry
        self.extension_registry.register_menu_item(
            "tools",  # Parent menu
            {
                "id": cell_monitor_id,
                "label": "JMS Cell Monitor",
                "tooltip": "Monitor robotic cell status in real-time",
                "enabled": True
            }
        )
        
        # JMS Cell Tests menu item
        cell_tests_id = "jms_cell_tests"
        event_system.subscribe("menu_item_clicked", cell_tests_id, self._on_cell_tests_clicked)
        self.menu_items.append(cell_tests_id)
        
        # Register menu item with the extension registry
        self.extension_registry.register_menu_item(
            "tools",  # Parent menu
            {
                "id": cell_tests_id,
                "label": "JMS Cell Tests",
                "tooltip": "Run tests on robotic cells",
                "enabled": True
            }
        )
        
        # JMS Integration Test menu item
        integration_test_id = "jms_integration_test"
        event_system.subscribe("menu_item_clicked", integration_test_id, self._on_integration_test_clicked)
        self.menu_items.append(integration_test_id)
        
        # Register menu item with the extension registry
        self.extension_registry.register_menu_item(
            "tools",  # Parent menu
            {
                "id": integration_test_id,
                "label": "JMS Integration Test",
                "tooltip": "Run integration test with robotic cell",
                "enabled": True
            }
        )
    
    def _on_jms_tools_clicked(self, menu_id: str) -> None:
        """
        Handle JMS Tools menu item click
        
        Args:
            menu_id: ID of the menu item
        """
        logger.info("JMS Tools menu item clicked")
        
        try:
            # Import the JMS tools dialog
            from ui.jms_tools_dialog import show_jms_tools_dialog
            
            # Show the dialog with default tab
            show_jms_tools_dialog(self.app_core.main_window, self.jms_service, 0)
        except Exception as e:
            logger.error(f"Failed to show JMS tools dialog: {str(e)}")
            event_system.publish("error", f"Failed to show JMS tools dialog: {str(e)}")
    
    def _on_cell_monitor_clicked(self, menu_id: str) -> None:
        """
        Handle JMS Cell Monitor menu item click
        
        Args:
            menu_id: ID of the menu item
        """
        logger.info("JMS Cell Monitor menu item clicked")
        
        try:
            # Import the JMS tools dialog
            from ui.jms_tools_dialog import show_jms_tools_dialog
            
            # Show the dialog with the monitoring tab selected (tab index 0)
            dialog = show_jms_tools_dialog(self.app_core.main_window, self.jms_service, 0)
        except Exception as e:
            logger.error(f"Failed to show JMS cell monitor: {str(e)}")
            event_system.publish("error", f"Failed to show JMS cell monitor: {str(e)}")
    
    def _on_cell_tests_clicked(self, menu_id: str) -> None:
        """
        Handle JMS Cell Tests menu item click
        
        Args:
            menu_id: ID of the menu item
        """
        logger.info("JMS Cell Tests menu item clicked")
        
        try:
            # Import the JMS tools dialog
            from ui.jms_tools_dialog import show_jms_tools_dialog
            
            # Show the dialog with the testing tab selected (tab index 1)
            dialog = show_jms_tools_dialog(self.app_core.main_window, self.jms_service, 1)
        except Exception as e:
            logger.error(f"Failed to show JMS cell tests: {str(e)}")
            event_system.publish("error", f"Failed to show JMS cell tests: {str(e)}")
    
    def _on_integration_test_clicked(self, menu_id: str) -> None:
        """
        Handle JMS Integration Test menu item click
        
        Args:
            menu_id: ID of the menu item
        """
        logger.info("JMS Integration Test menu item clicked")
        
        try:
            # Import the JMS tools dialog
            from ui.jms_tools_dialog import show_jms_tools_dialog
            
            # Show the dialog with the integration tab selected (tab index 2)
            dialog = show_jms_tools_dialog(self.app_core.main_window, self.jms_service, 2)
        except Exception as e:
            logger.error(f"Failed to show JMS integration test: {str(e)}")
            event_system.publish("error", f"Failed to show JMS integration test: {str(e)}")

# Module instance
module_instance = JMSToolsExtensionModule()