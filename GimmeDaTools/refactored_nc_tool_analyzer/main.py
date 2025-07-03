#!/usr/bin/env python3
"""
NC Tool Analyzer - Main Entry Point
A complete tool analysis system with automatic machine communication
"""

import tkinter as tk
import traceback
import sys
import os

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

def show_error(title, message):
    """Show error dialog"""
    import tkinter.messagebox as messagebox
    messagebox.showerror(title, message)

def main():
    """Main entry point for the application"""
    try:
        logger.info("Starting application")
        
        # Import here to catch import errors
        from ui.main_window import MainWindow
        
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()
        
    except Exception as e:
        error_msg = f"Error starting application: {str(e)}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        show_error("Startup Error", f"Error starting application: {str(e)}\n\nSee app.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()