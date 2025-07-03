# NC Tool Analyzer

A complete tool analysis system with automatic machine communication for CNC machines.

## Overview

The NC Tool Analyzer is a Python application that helps CNC machine operators and programmers analyze NC files and check tool availability across multiple machines. It provides a user-friendly interface for managing machines, analyzing NC files, and sending files to machines.

## Features

- **Machine Management**: Add, edit, and delete machine configurations
- **Tool Analysis**: Analyze NC files for tool requirements
- **Machine Compatibility**: Check tool availability across all configured machines
- **Tool Life Tracking**: Monitor tool usage and get warnings for critical tools
- **File Transfer**: Send NC files directly to machines
- **Detailed Results**: View detailed analysis results including tool sequences, stock dimensions, and more

## Architecture

The application follows a modular, object-oriented architecture with clear separation of concerns:

### Models

- `Machine`: Represents a CNC machine with its properties and tools
- `Tool`: Represents a CNC tool with its properties and life data
- `AnalysisResult`: Represents the result of analyzing an NC file

### Services

- `MachineService`: Handles machine management and communication
- `AnalysisService`: Handles NC file analysis and machine compatibility checks

### UI Components

- `MainWindow`: Main application window
- `AnalysisTab`: Tab for analyzing NC files
- `MachineTab`: Tab for managing machines
- `ResultsTab`: Tab for viewing detailed analysis results

### Utilities

- `EventSystem`: Simple event system for communication between components
- `FileUtils`: Utilities for file operations

## Event System

The application uses a simple event system for communication between components. This allows for loose coupling between components and makes the code more maintainable.

Events include:
- `machines_loaded`: Fired when machines are loaded from the database
- `machines_saved`: Fired when machines are saved to the database
- `machine_added`: Fired when a machine is added to the database
- `machine_updated`: Fired when a machine is updated
- `machine_deleted`: Fired when a machine is deleted
- `analysis_complete`: Fired when NC file analysis is complete
- `file_sent`: Fired when a file is sent to a machine
- `error`: Fired when an error occurs

## Getting Started

1. Install Python 3.6 or higher
2. Install required packages: `tkinter`
3. Run the application: `python main.py`

## Usage

1. Add machines in the "Machine Management" tab
2. Click "Refresh All Machines" to download current tool data
3. Upload an NC file in the "Analysis" tab to see tool availability across all machines
4. View detailed results in the "Results" tab
5. Send the NC file to a compatible machine

## Requirements

- Python 3.6 or higher
- Tkinter
- TNCremo (for machine communication)

## Future Enhancements

- Integration with JMS 4.0 API for real-time machine data
- Machine Shop Scheduler for visual scheduling of jobs across machines
- Support for more machine types and communication protocols
- Enhanced tool life management
- Database backend for better performance with larger datasets