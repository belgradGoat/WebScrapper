# NC Tool Analyzer

A complete tool analysis system with automatic machine communication and scheduling capabilities.

## Overview

NC Tool Analyzer is a Python application that helps machine shops analyze NC programs, manage machines and tools, and schedule jobs. It features a modular architecture that allows for easy extension and customization.

## Features

- Analyze NC programs to determine required tools
- Check tool availability across multiple machines
- Manage machine configurations and tool libraries
- Schedule jobs and parts for production
- Integration with Job Management System (JMS)
- Modular architecture for easy extension

## Modular Architecture

The application uses a plugin-based architecture that allows for easy extension and customization. The core components are:

### Module System

The module system provides the infrastructure for discovering, loading, and managing modules. It consists of:

- **Module Interface**: Base interface that all modules must implement
- **Module Registry**: Discovers and manages modules
- **Service Registry**: Provides dependency injection for modules
- **Extension Registry**: Allows modules to extend functionality at specific points
- **Config Manager**: Manages application and module configuration

### Core Modules

The application comes with several core modules:

#### Service Modules

- **Machine Service**: Manages machines and their tools
- **Analysis Service**: Analyzes NC files to determine required tools
- **Scheduler Service**: Manages job and part scheduling
- **JMS Service**: Provides integration with Job Management System

#### Tab Modules

- **Analysis Tab**: Provides the UI for analyzing NC files
- **Machine Tab**: Provides the UI for managing machines
- **Results Tab**: Provides the UI for viewing analysis results
- **Scheduler Tab**: Provides the UI for scheduling jobs and parts

### User Modules

Users can create their own modules to extend the application. An example module is provided to demonstrate how to create a custom module.

## Creating Custom Modules

To create a custom module, you need to implement one of the module interfaces:

- **ModuleInterface**: Base interface for all modules
- **TabModuleInterface**: Interface for modules that provide UI tabs
- **ServiceModuleInterface**: Interface for modules that provide services

Here's an example of a simple tab module:

```python
from module_system.module_interface import TabModuleInterface

class MyCustomModule(TabModuleInterface):
    def get_name(self):
        return "my_custom_module"
        
    def get_version(self):
        return "1.0.0"
        
    def get_description(self):
        return "My custom module"
        
    def get_required_services(self):
        return ["machine_service"]
        
    def initialize(self, service_registry):
        self.machine_service = service_registry.get_service("machine_service")
        
    def get_tab(self, parent):
        # Create and return a tab frame
        frame = ttk.Frame(parent)
        ttk.Label(frame, text="My Custom Tab").pack()
        return frame
        
    def get_tab_name(self):
        return "My Tab"
        
    def get_tab_icon(self):
        return "🔧"
```

Save your module in the `modules` directory, and it will be automatically discovered and loaded when the application starts.

## Configuration

The application configuration is stored in `config.json`. You can use this file to enable or disable modules, set module-specific configuration, and more.

```json
{
    "app": {
        "name": "NC Tool Analyzer",
        "version": "1.0.0"
    },
    "modules": {
        "my_custom_module": {
            "enabled": true,
            "custom_setting": "value"
        }
    }
}
```

## Extension Points

The application provides several extension points that modules can use to extend functionality:

- **app.startup**: Called when the application starts
- **app.shutdown**: Called when the application shuts down
- **ui.menu.file**: Allows adding items to the File menu
- **ui.menu.tools**: Allows adding items to the Tools menu
- **ui.menu.help**: Allows adding items to the Help menu
- **ui.toolbar**: Allows adding items to the toolbar
- **ui.statusbar**: Allows adding items to the status bar

To register a handler for an extension point, use the extension registry:

```python
def initialize(self, service_registry):
    extension_registry = service_registry.get_service("extension_registry")
    tools_menu_ext = extension_registry.get_extension_point("ui.menu.tools")
    tools_menu_ext.register_handler(self._add_tools_menu_items)
    
def _add_tools_menu_items(self, menu):
    menu.add_command(label="My Tool", command=self._my_tool)
```

## Requirements

- Python 3.6 or higher
- Tkinter
- Requests (optional, for JMS integration)

## Installation

1. Clone the repository
2. Install the required packages: `pip install -r requirements.txt`
3. Run the application: `python main.py`