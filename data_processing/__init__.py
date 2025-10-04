"""
Data Processing Module

This module contains all data processing and cleansing functionality including:
- Data cleansing utilities
- Data format standardization
- Data validation
"""

from .data_cleaner import DataCleaner

# Create a compatibility function
def cleanse_all_data(data_directory: str = "data"):
    """Compatibility function for the old data_cleaner interface"""
    cleanser = DataCleaner(data_directory)
    return cleanser.cleanse_all_files()

__all__ = [
    'DataCleaner',
    'cleanse_all_data'
]
