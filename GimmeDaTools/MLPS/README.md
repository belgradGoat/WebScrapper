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
- **JMS Service**: Provides integration with Job Management System (see [JMS Integration](#jms-integration) for details)

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

## JMS Integration

The application includes integration with Job Management System (JMS) through a modular architecture. This allows for easy configuration and extension of JMS functionality.

### JMS Modules

JMS functionality is provided through two modules:

1. **JMSServiceModule**: Core module that provides the JMS service functionality
   - Located in `core_modules/services/jms_service_module.py`
   - Implements the `ServiceModuleInterface`
   - Provides methods for enabling/disabling JMS integration
   - Handles connection to the JMS API

2. **JMSMenuExtensionModule**: UI integration module for JMS configuration
   - Located in `core_modules/services/jms_menu_extension_module.py`
   - Adds the "JMS Configuration" option to the Tools menu
   - Opens the JMS configuration dialog

### Module Loading Process

The JMS modules are loaded through the module system:

1. The `ApplicationCore` initializes the `ModuleRegistry` during startup
2. The `ModuleRegistry` scans the `core_modules` directory for modules
3. It finds and loads the JMS modules
4. The modules are initialized in dependency order:
   - `scheduler_service_module` (dependency of JMS)
   - `jms_service_module`
   - `jms_menu_extension_module`

### Configuration

JMS configuration is stored in `config.json`:

```json
"jms_service_module": {
    "enabled": true,
    "base_url": "http://localhost:8080"
}
```

You can enable/disable JMS integration by changing the `enabled` property.

### UI Integration

The JMS UI integration provides multiple ways to access JMS functionality:

1. **Tools Menu > JMS Configuration**: Direct access to JMS configuration
   - Added by both the MainWindow and the JMSMenuExtensionModule
   - Opens the JMSConfigDialog for configuring JMS connection

2. **Tools Menu > Settings > JMS Tab**: Access through the Settings dialog
   - The Settings dialog includes a dedicated JMS tab
   - Provides options to enable/disable JMS integration
   - Allows configuring the JMS API URL
   - Includes a "Test Connection" button

3. **Extension Point System**:
   - The `JMSMenuExtensionModule` registers a handler for the `ui.menu.tools` extension point
   - When the main window creates the Tools menu, it invokes this extension point
   - The handler adds the "JMS Configuration" menu item to the Tools menu

### Error Handling

The JMS modules include error handling to gracefully handle cases where JMS is not available:

1. If the `requests` package is not installed, JMS functionality is disabled
2. If JMS initialization fails, an error is logged but the application continues
3. The UI adapts to show appropriate error messages

### Benefits of the Modular Approach

This modular approach provides several benefits:

1. **Decoupling**: JMS functionality is completely decoupled from the core application
2. **Configurability**: JMS can be enabled/disabled through configuration
3. **Extensibility**: New JMS features can be added without modifying core code
4. **Error Isolation**: JMS errors don't affect the rest of the application
5. **Dependency Management**: Dependencies are automatically resolved

### Creating Custom JMS Extensions

You can create custom JMS extensions by implementing the `ModuleInterface`:

```python
from module_system.module_interface import ModuleInterface

class MyJMSExtension(ModuleInterface):
    def get_name(self):
        return "my_jms_extension"
        
    def get_required_services(self):
        return ["jms_service"]
        
    def initialize(self, service_registry):
        self.jms_service = service_registry.get_service("jms_service")
        # Add your custom JMS functionality here
```

Save your extension in the `modules` directory, and it will be automatically discovered and loaded when the application starts.