#!/usr/bin/env python3
"""
Migration utility to help transition from JSON-based storage to SQLite database.
Provides tools to backup, migrate, and verify data integrity.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Tuple
from pathlib import Path

from ui.data_storage.storage_adapter import SQLiteStorageAdapter, JSONStorageAdapter


class MigrationManager:
    """Manages migration from JSON to SQLite storage"""

    def __init__(self, json_file: str = 'bets.json', db_file: str = 'betting_data.db'):
        """
        Initialize migration manager.

        Args:
            json_file: Path to JSON file
            db_file: Path to SQLite database file
        """
        self.json_file = json_file
        self.db_file = db_file
        self.backup_dir = '.backups'
        self._ensure_backup_dir()

    def _ensure_backup_dir(self):
        """Ensure backup directory exists"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self) -> Tuple[bool, str]:
        """
        Create a backup of the JSON file before migration.

        Returns:
            Tuple of (success, backup_path)
        """
        if not os.path.exists(self.json_file):
            return False, "JSON file not found"

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(
                self.backup_dir,
                f'bets_backup_{timestamp}.json'
            )
            shutil.copy(self.json_file, backup_file)
            return True, backup_file
        except Exception as e:
            return False, f"Backup failed: {e}"

    def validate_json_data(self) -> Tuple[bool, List[str]]:
        """
        Validate JSON data structure and integrity.

        Returns:
            Tuple of (valid, list_of_issues)
        """
        issues = []

        if not os.path.exists(self.json_file):
            return False, ["JSON file not found"]

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        except Exception as e:
            return False, [f"Error reading JSON: {e}"]

        if not isinstance(data, list):
            issues.append("Root element is not a list")
            return False, issues

        # Validate each bet
        required_fields = ['id', 'placement_date', 'match_date', 'stake', 'odds', 'status']
        for idx, bet in enumerate(data):
            if not isinstance(bet, dict):
                issues.append(f"Bet {idx} is not a dictionary")
                continue

            for field in required_fields:
                if field not in bet:
                    issues.append(f"Bet {idx} missing required field: {field}")

        return len(issues) == 0, issues

    def migrate(self, verify: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Perform complete migration from JSON to SQLite.

        Args:
            verify: Whether to verify data after migration

        Returns:
            Tuple of (success, message, stats)
        """
        stats = {
            'backup_created': False,
            'backup_path': None,
            'json_records': 0,
            'migrated_records': 0,
            'failed_records': [],
            'verification_passed': False,
            'db_records_after': 0
        }

        # Step 1: Validate JSON
        print("Step 1: Validating JSON data...")
        valid, issues = self.validate_json_data()
        if not valid:
            return False, "JSON validation failed: " + "; ".join(issues), stats

        # Step 2: Create backup
        print("Step 2: Creating backup...")
        success, backup_path = self.create_backup()
        if success:
            stats['backup_created'] = True
            stats['backup_path'] = backup_path
            print(f"  ✓ Backup created: {backup_path}")
        else:
            return False, f"Backup failed: {backup_path}", stats

        # Step 3: Load JSON data
        print("Step 3: Loading JSON data...")
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                bets = json.load(f)
            stats['json_records'] = len(bets)
            print(f"  ✓ Loaded {len(bets)} records from JSON")
        except Exception as e:
            return False, f"Failed to load JSON: {e}", stats

        # Step 4: Migrate to SQLite
        print("Step 4: Migrating to SQLite...")
        sqlite_adapter = SQLiteStorageAdapter(self.db_file)

        failed_records = []
        for idx, bet in enumerate(bets):
            try:
                sqlite_adapter.add_bet(bet)
                stats['migrated_records'] += 1
            except Exception as e:
                failed_records.append({
                    'index': idx,
                    'error': str(e),
                    'bet_id': bet.get('id', 'unknown')
                })

        stats['failed_records'] = failed_records

        if failed_records:
            msg = f"Migrated {stats['migrated_records']} records, {len(failed_records)} failed"
            print(f"  ⚠ {msg}")
        else:
            print(f"  ✓ Migrated {stats['migrated_records']} records")

        # Step 5: Verify migration
        if verify:
            print("Step 5: Verifying migration...")
            try:
                all_bets = sqlite_adapter.get_all_bets()
                stats['db_records_after'] = len(all_bets)

                if len(all_bets) == stats['json_records']:
                    stats['verification_passed'] = True
                    print(f"  ✓ Verification passed: {len(all_bets)} records in database")
                else:
                    msg = f"Record count mismatch: JSON={stats['json_records']}, DB={len(all_bets)}"
                    print(f"  ⚠ {msg}")
            except Exception as e:
                print(f"  ✗ Verification failed: {e}")

        # Step 6: Summary
        if failed_records:
            return False, f"Migration completed with {len(failed_records)} errors", stats
        else:
            return True, "Migration successful", stats

    def rollback(self, backup_path: str) -> Tuple[bool, str]:
        """
        Rollback migration by restoring from backup.

        Args:
            backup_path: Path to backup file

        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(backup_path):
            return False, "Backup file not found"

        try:
            shutil.copy(backup_path, self.json_file)
            return True, f"Restored from backup: {backup_path}"
        except Exception as e:
            return False, f"Rollback failed: {e}"

    def compare_data(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare data between JSON and SQLite.

        Returns:
            Tuple of (match, comparison_details)
        """
        comparison = {
            'json_count': 0,
            'db_count': 0,
            'match': False,
            'sample_differences': []
        }

        # Load JSON
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                json_bets = json.load(f)
            comparison['json_count'] = len(json_bets)
        except Exception as e:
            return False, {'error': f"Failed to load JSON: {e}"}

        # Load SQLite
        try:
            sqlite_adapter = SQLiteStorageAdapter(self.db_file)
            db_bets = sqlite_adapter.get_all_bets()
            comparison['db_count'] = len(db_bets)
        except Exception as e:
            return False, {'error': f"Failed to load database: {e}"}

        # Check counts
        if comparison['json_count'] != comparison['db_count']:
            comparison['match'] = False
        else:
            comparison['match'] = True

        return comparison['match'], comparison


def run_migration_interactive():
    """Run interactive migration process"""
    print("\n" + "="*60)
    print("Betting Data Migration: JSON → SQLite")
    print("="*60 + "\n")


    current_folder = os.path.dirname(__file__)

    json_file = '../bets.json'
    db_file = '../betting_data.db'

    if not os.path.exists(json_file):
        print(f"✗ JSON file not found: {json_file}")
        return

    print(f"JSON file: {json_file}")
    print(f"Target database: {db_file}\n")

    # Confirm migration
    response = input("Proceed with migration? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return

    # Run migration
    manager = MigrationManager(json_file, db_file)
    success, message, stats = manager.migrate(verify=True)

    print("\n" + "="*60)
    print("Migration Summary")
    print("="*60)
    print(f"Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
    print(f"Message: {message}")
    print(f"JSON records: {stats['json_records']}")
    print(f"Migrated records: {stats['migrated_records']}")
    print(f"Failed records: {len(stats['failed_records'])}")
    print(f"Database records: {stats['db_records_after']}")
    print(f"Verification: {'✓ PASSED' if stats['verification_passed'] else '⚠ NOT VERIFIED'}")

    if stats['backup_created']:
        print(f"Backup created: {stats['backup_path']}")

    if stats['failed_records']:
        print("\nFailed records:")
        for failed in stats['failed_records'][:5]:  # Show first 5
            print(f"  - Bet ID {failed['bet_id']}: {failed['error']}")
        if len(stats['failed_records']) > 5:
            print(f"  ... and {len(stats['failed_records']) - 5} more")

    print("="*60 + "\n")


if __name__ == '__main__':
    run_migration_interactive()

