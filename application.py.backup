#!/usr/bin/env python3
"""
Entry point for Elastic Beanstalk.
"""

# Add the project root to the path to allow imports.
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.simple_app import application

if __name__ == '__main__':
    # This allows running the app locally for testing,
    # but EB will use the 'application' object directly.
    application.run()

