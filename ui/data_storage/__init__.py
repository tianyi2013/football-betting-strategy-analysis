#!/usr/bin/env python3
"""
Data Storage Module

Provides robust SQLite and JSON-based storage for betting data.
"""

from .database_models import BetRepository, DatabaseManager
from .migration import MigrationManager
from .storage_adapter import (
    JSONStorageAdapter,
    SQLiteStorageAdapter,
    StorageAdapter,
    StorageFactory,
    get_storage_adapter,
)

__all__ = [
    # Database models
    'DatabaseManager',
    'BetRepository',
    # Storage adapters
    'get_storage_adapter',
    'StorageFactory',
    'StorageAdapter',
    'SQLiteStorageAdapter',
    'JSONStorageAdapter',
    # Migration
    'MigrationManager'
]

