#!/usr/bin/env python3
"""
Data Storage Module

Provides robust SQLite and JSON-based storage for betting data.
"""

from .database_models import (
    DatabaseManager,
    BetRepository
)
from .storage_adapter import (
    get_storage_adapter,
    StorageFactory,
    StorageAdapter,
    SQLiteStorageAdapter,
    JSONStorageAdapter
)
from .migration import MigrationManager

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

