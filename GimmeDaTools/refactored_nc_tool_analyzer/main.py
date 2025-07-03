#!/usr/bin/env python3
"""
NC Tool Analyzer - Main Entry Point
A complete tool analysis system with automatic machine communication
"""

import tkinter as tk
import traceback
import sys
import os
import importlib.util

# Add error logging
def setup_logging():
    """Set up logging to file"""
    import logging
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, "app.log")
    
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger("main")

logger = setup_logging()

# Log system information
logger.info("Python version: %s", sys.version)
logger.info("Python executable: %s", sys.executable)
logger.info("Python path: %s", sys.path)

# Check for requests module
try:
    spec = importlib.util.find_spec("requests")
    if spec:
        logger.info("Found requests module spec at: %s", spec.origin)
        import requests
        logger.info("Successfully imported requests module from: %s", requests.__file__)
        logger.info("Requests version: %s", requests.__version__)
    else:
        logger.warning("No requests module spec found")
except Exception as e:
    logger.error("Error checking for requests module: %s", str(e))

def show_error(title, message):
    """Show error dialog"""
    import tkinter.messagebox as messagebox
    messagebox.showerror(title, message)

def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting application")
        
        # Import here to catch import errors
        from application_core import ApplicationCore
        from ui.main_window import MainWindow
        
        # Initialize the application core
        logger.info("Initializing application core")
        app_core = ApplicationCore()
        if not app_core.initialize():
            logger.error("Failed to initialize application core")
            show_error("Startup Error", "Failed to initialize application core.\n\nSee app.log for details.")
            sys.exit(1)
        
        # Create the main window
        logger.info("Creating main window")
        root = tk.Tk()
        app = MainWindow(root, app_core)
        
        # Run the application
        logger.info("Running application")
        root.mainloop()
        
        # Shutdown the application core
        logger.info("Shutting down application core")
        app_core.shutdown()
        
    except Exception as e:
        error_msg = f"Error starting application: {str(e)}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        show_error("Startup Error", f"Error starting application: {str(e)}\n\nSee app.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()