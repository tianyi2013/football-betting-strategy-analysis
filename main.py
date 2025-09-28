#!/usr/bin/env python3
"""
Main entry point for the unified betting strategy application.
This replaces both main_app.py and multi_league_app.py with a single unified interface.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the unified application
from app.unified_app import main

if __name__ == "__main__":
    main()