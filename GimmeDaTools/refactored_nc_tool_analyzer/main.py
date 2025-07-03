#!/usr/bin/env python3
"""
NC Tool Analyzer - Main Entry Point
A complete tool analysis system with automatic machine communication
"""

import tkinter as tk
from ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()