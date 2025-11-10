#!/usr/bin/env python3
"""
Data Cleansing Module for Premier League Betting Data

This module provides data cleansing functionality to standardize all date formats 
across all data files to yyyy-mm-dd format. This eliminates the need for complex 
date parsing logic in the strategy code.
"""

import glob
import os
from typing import Dict, Tuple

import pandas as pd


class DataCleaner:
    """
    Handles data cleansing operations for Premier League betting data.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the data cleaner.
        
        Args:
            data_directory (str): Path to directory containing data files
        """
        self.data_directory = data_directory
    
    def cleanse_date_format(self, file_path: str) -> Tuple[bool, str]:
        """
        Cleanse date format in a single CSV file.
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            print(f"Processing {file_path}...")
            
            # Read the CSV file
            df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')
            
            # Check if Date column exists
            if 'Date' not in df.columns:
                message = f"No 'Date' column found in {file_path}"
                print(f"  [WARNING]  {message}")
                return False, message
            
            # Store original date format for logging
            original_dates = df['Date'].head(3).tolist()
            
            # Ensure string and strip spaces
            df['Date'] = df['Date'].astype(str).str.strip()

            # Try different date formats (with and without time) and convert to yyyy-mm-dd
            date_formats = [
                '%d/%m/%Y %H:%M',  # 16/08/2024 20:30
                '%d/%m/%y %H:%M',  # 16/08/05 20:30
                '%d/%m/%Y',        # 16/08/2024
                '%d/%m/%y',        # 16/08/05
                '%Y-%m-%d %H:%M',  # 2024-08-16 20:30
                '%Y-%m-%d',        # 2024-08-16 (already correct)
                '%d-%m-%Y %H:%M',  # 16-08-2024 20:30
                '%d-%m-%y %H:%M',  # 16-08-05 20:30
                '%d-%m-%Y',        # 16-08-2024
                '%d-%m-%y',        # 16-08-05
            ]
            
            converted = False
            for fmt in date_formats:
                try:
                    # Create a copy to test the format
                    test_df = df.copy()
                    test_df['Date'] = pd.to_datetime(test_df['Date'], format=fmt, errors='coerce')
                    
                    # Check if this format worked (fewer NaT values)
                    na_count = test_df['Date'].isna().sum()
                    if na_count < len(test_df) * 0.5:  # Less than 50% NaT values
                        df['Date'] = test_df['Date']
                        converted = True
                        break
                except Exception:
                    continue
            
            # Fallback: general day-first parse (handles mixed DD/MM/YYYY[ HH:MM])
            if not converted:
                try:
                    test_df = df.copy()
                    test_df['Date'] = pd.to_datetime(test_df['Date'], dayfirst=True, errors='coerce')
                    na_count = test_df['Date'].isna().sum()
                    if na_count < len(test_df) * 0.5:
                        df['Date'] = test_df['Date']
                        converted = True
                except Exception:
                    pass

            if not converted:
                message = f"Could not parse dates in {file_path}"
                print(f"  [ERROR] {message}")
                return False, message
            
            # Convert to yyyy-mm-dd string format (drop time component)
            df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

            # Save the cleansed data back to the file
            df.to_csv(file_path, index=False, encoding='utf-8')
            
            message = f"Converted {original_dates} -> {df['Date'].head(3).tolist()}"
            print(f"  [SUCCESS] {message}")
            return True, message
            
        except Exception as e:
            message = f"Error processing {file_path}: {str(e)}"
            print(f"  [ERROR] {message}")
            return False, message
    
    def cleanse_all_files(self) -> Dict[str, int]:
        """
        Cleanse all CSV files in the data directory.
        
        Returns:
            Dict[str, int]: Summary of cleansing results
        """
        print("[CLEANSE] Premier League Data Cleansing Script")
        print("=" * 50)
        
        # Find all CSV files in the data directory
        if not os.path.exists(self.data_directory):
            print(f"[ERROR] Data directory '{self.data_directory}' not found!")
            return {'successful': 0, 'failed': 0, 'total': 0}
        
        csv_files = glob.glob(os.path.join(self.data_directory, "*.csv"))
        
        if not csv_files:
            print(f"[ERROR] No CSV files found in '{self.data_directory}' directory!")
            return {'successful': 0, 'failed': 0, 'total': 0}
        
        print(f"[FILES] Found {len(csv_files)} CSV files to process")
        print()
        
        # Process each file
        successful = 0
        failed = 0
        
        for file_path in sorted(csv_files):
            success, _ = self.cleanse_date_format(file_path)
            if success:
                successful += 1
            else:
                failed += 1
            print()
        
        # Summary
        print("=" * 50)
        print("[SUMMARY] CLEANSING SUMMARY")
        print("=" * 50)
        print(f"[SUCCESS] Successfully processed: {successful} files")
        print(f"[ERROR] Failed to process: {failed} files")
        print(f"[FILES] Total files: {len(csv_files)} files")
        
        if successful == len(csv_files):
            print("\n[SUCCESS] All files processed successfully!")
            print("[DATE] All date formats are now standardized to yyyy-mm-dd")
            print("[TOOL] Strategy code can now use simple date parsing")
        else:
            print(f"\n[WARNING]  {failed} files failed to process. Check the errors above.")
        
        return {
            'successful': successful,
            'failed': failed,
            'total': len(csv_files)
        }


def cleanse_all_data(data_directory: str = "data/premier_league") -> Dict[str, int]:
    """
    Convenience function to cleanse all data files.
    
    Args:
        data_directory (str): Path to directory containing data files
        
    Returns:
        Dict[str, int]: Summary of cleansing results
    """
    cleaner = DataCleaner(data_directory)
    return cleaner.cleanse_all_files()


def main():
    """Main function to run data cleansing."""
    try:
        cleanse_all_data()
    except KeyboardInterrupt:
        print("\nGoodbye! [GOODBYE]")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
