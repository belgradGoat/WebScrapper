"""
Configuration Manager for NC Tool Analyzer
Provides a system for storing and retrieving configuration values
"""
import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manager for application and module configuration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = {}
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config.json"
        )
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.info(f"Configuration file {self.config_path} not found, using defaults")
                self.config = {
                    "app": {
                        "name": "NC Tool Analyzer",
                        "version": "1.0.0"
                    },
                    "modules": {}
                }
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            self.config = {
                "app": {
                    "name": "NC Tool Analyzer",
                    "version": "1.0.0"
                },
                "modules": {}
            }
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            key: Configuration key (dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        parts = key.split('.')
        config = self.config
        
        for part in parts:
            if part in config:
                config = config[part]
            else:
                return default
        
        return config
    
    def set_value(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            key: Configuration key (dot notation for nested keys)
            value: Value to set
        """
        parts = key.split('.')
        config = self.config
        
        # Navigate to the correct nested dictionary
        for i, part in enumerate(parts[:-1]):
            if part not in config:
                config[part] = {}
            config = config[part]
        
        # Set the value
        config[parts[-1]] = value
        
        # Save the configuration
        self.save_config()
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific module
        
        Args:
            module_name: Name of the module
            
        Returns:
            Module configuration dictionary
        """
        if "modules" not in self.config:
            self.config["modules"] = {}
        
        if module_name not in self.config["modules"]:
            self.config["modules"][module_name] = {}
        
        return self.config["modules"][module_name]