#!/usr/bin/env python3
"""
Data storage adapter providing a unified interface for betting data persistence.
Supports both SQLite (default) and JSON file-based storage for compatibility.
"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .database_models import BetRepository, DatabaseManager


class StorageAdapter(ABC):
    """Abstract base class for storage adapters"""

    @abstractmethod
    def add_bet(self, bet_data: Dict[str, Any]) -> Any:
        """Add a new bet"""
        pass

    @abstractmethod
    def get_all_bets(self) -> List[Dict[str, Any]]:
        """Get all bets"""
        pass

    @abstractmethod
    def update_bet(self, bet_id: Any, update_data: Dict[str, Any]) -> bool:
        """Update a bet"""
        pass

    @abstractmethod
    def delete_bet(self, bet_id: Any) -> bool:
        """Delete a bet"""
        pass

    @abstractmethod
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics"""
        pass

    @abstractmethod
    def get_bet_by_id(self, bet_id: Any) -> Optional[Dict[str, Any]]:
        """Get a bet by ID"""
        pass


class SQLiteStorageAdapter(StorageAdapter):
    """SQLite-based storage adapter (recommended)"""

    def __init__(self, db_path: str = 'betting_data.db'):
        """
        Initialize SQLite storage adapter.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_manager = DatabaseManager(db_path)
        self.bets_repo = BetRepository(self.db_manager)

    def add_bet(self, bet_data: Dict[str, Any]) -> int:
        """Add a new bet to SQLite"""
        return self.bets_repo.add_bet(bet_data)

    def get_all_bets(self) -> List[Dict[str, Any]]:
        """Get all bets from SQLite"""
        return self.bets_repo.get_all_bets()

    def get_bets_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get bets filtered by status"""
        return self.bets_repo.get_bets_by_status(status)

    def get_bets_by_league(self, league: str) -> List[Dict[str, Any]]:
        """Get bets filtered by league"""
        return self.bets_repo.get_bets_by_league(league)

    def get_bets_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get bets within date range"""
        return self.bets_repo.get_bets_by_date_range(start_date, end_date)

    def update_bet(self, bet_id: int, update_data: Dict[str, Any]) -> bool:
        """Update a bet in SQLite"""
        return self.bets_repo.update_bet(bet_id, update_data)

    def delete_bet(self, bet_id: int) -> bool:
        """Delete a bet from SQLite"""
        return self.bets_repo.delete_bet(bet_id)

    def get_bet_by_id(self, bet_id: int) -> Optional[Dict[str, Any]]:
        """Get a single bet by ID"""
        return self.bets_repo.get_bet_by_id(bet_id)

    def get_analytics(self) -> Dict[str, Any]:
        """
        Calculate current analytics from bets data.
        Analytics are calculated on-the-fly, not stored in database.
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) as total FROM bets')
            total_bets = cursor.fetchone()['total']

            cursor.execute("SELECT COUNT(*) as won FROM bets WHERE status = 'won'")
            won_bets = cursor.fetchone()['won']

            cursor.execute("SELECT COUNT(*) as lost FROM bets WHERE status = 'lost'")
            lost_bets = cursor.fetchone()['lost']

            cursor.execute("SELECT COUNT(*) as pending FROM bets WHERE status = 'pending'")
            pending_bets = cursor.fetchone()['pending']

            cursor.execute('SELECT COALESCE(SUM(stake), 0) as total FROM bets')
            total_stake = cursor.fetchone()['total']

            cursor.execute('SELECT COALESCE(SUM(profit), 0) as total FROM bets')
            total_profit = cursor.fetchone()['total']

            cursor.execute('SELECT COALESCE(AVG(odds), 0) as avg FROM bets')
            average_odds = cursor.fetchone()['avg']

            win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0

            return {
                'total_bets': total_bets,
                'won_bets': won_bets,
                'lost_bets': lost_bets,
                'pending_bets': pending_bets,
                'win_rate': round(win_rate, 1),
                'total_stake': round(total_stake, 2),
                'total_profit': round(total_profit, 2),
                'average_odds': round(average_odds, 2),
                'roi': round((total_profit / total_stake * 100) if total_stake > 0 else 0, 1)
            }

    def migrate_from_json(self, json_file_path: str) -> bool:
        """
        Migrate data from JSON file to SQLite.

        Args:
            json_file_path: Path to JSON file to migrate from

        Returns:
            True if successful
        """
        if not os.path.exists(json_file_path):
            print(f"JSON file not found: {json_file_path}")
            return False

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                bets_list = json.load(f)

            return self.bets_repo.replace_all_bets(bets_list)
        except Exception as e:
            print(f"Error migrating from JSON: {e}")
            return False



class JSONStorageAdapter(StorageAdapter):
    """JSON file-based storage adapter (for backward compatibility)"""

    def __init__(self, file_path: str = 'bets.json'):
        """
        Initialize JSON storage adapter.

        Args:
            file_path: Path to JSON file
        """
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure JSON file exists"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)

    def _load_data(self) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return []

    def _save_data(self, data: List[Dict[str, Any]]):
        """Save data to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving JSON data: {e}")

    def add_bet(self, bet_data: Dict[str, Any]) -> Any:
        """Add a new bet to JSON file"""
        data = self._load_data()
        bet_data['id'] = int(datetime.now().timestamp() * 1000)
        data.append(bet_data)
        self._save_data(data)
        return bet_data['id']

    def get_all_bets(self) -> List[Dict[str, Any]]:
        """Get all bets from JSON file"""
        return self._load_data()

    def update_bet(self, bet_id: Any, update_data: Dict[str, Any]) -> bool:
        """Update a bet in JSON file"""
        data = self._load_data()
        for bet in data:
            if bet.get('id') == bet_id:
                bet.update(update_data)
                bet['updated_at'] = datetime.now().isoformat()
                self._save_data(data)
                return True
        return False

    def delete_bet(self, bet_id: Any) -> bool:
        """Delete a bet from JSON file"""
        data = self._load_data()
        filtered = [bet for bet in data if bet.get('id') != bet_id]
        if len(filtered) < len(data):
            self._save_data(filtered)
            return True
        return False

    def get_bet_by_id(self, bet_id: Any) -> Optional[Dict[str, Any]]:
        """Get a bet by ID from JSON file"""
        data = self._load_data()
        for bet in data:
            if bet.get('id') == bet_id:
                return bet
        return None

    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics from JSON data"""
        bets = self._load_data()
        total_bets = len(bets)
        won_bets = len([b for b in bets if b.get('status') == 'won'])
        lost_bets = len([b for b in bets if b.get('status') == 'lost'])
        pending_bets = len([b for b in bets if b.get('status') == 'pending'])

        total_stake = sum(b.get('stake', 0) for b in bets)
        total_profit = sum(b.get('profit', 0) for b in bets)

        avg_odds = sum(b.get('odds', 0) for b in bets) / total_bets if total_bets > 0 else 0
        win_rate = (won_bets / total_bets * 100) if total_bets > 0 else 0
        roi = (total_profit / total_stake * 100) if total_stake > 0 else 0

        return {
            'total_bets': total_bets,
            'won_bets': won_bets,
            'lost_bets': lost_bets,
            'pending_bets': pending_bets,
            'win_rate': round(win_rate, 1),
            'total_stake': round(total_stake, 2),
            'total_profit': round(total_profit, 2),
            'average_odds': round(avg_odds, 2),
            'roi': round(roi, 1)
        }


class StorageFactory:
    """Factory for creating appropriate storage adapters"""

    @staticmethod
    def create_adapter(storage_type: str = 'sqlite', **kwargs) -> StorageAdapter:
        """
        Create a storage adapter.

        Args:
            storage_type: Type of storage ('sqlite' or 'json')
            **kwargs: Additional arguments for the adapter

        Returns:
            StorageAdapter instance
        """
        if storage_type.lower() == 'sqlite':
            db_path = kwargs.get('db_path', 'betting_data.db')
            return SQLiteStorageAdapter(db_path)
        elif storage_type.lower() == 'json':
            file_path = kwargs.get('file_path', 'bets.json')
            return JSONStorageAdapter(file_path)
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")


# Convenience function for getting the default storage adapter
_default_adapter = None

def get_storage_adapter(storage_type: str = 'sqlite', **kwargs) -> StorageAdapter:
    """
    Get or create a storage adapter instance.

    Uses caching for the default adapter to avoid creating multiple connections.

    Args:
        storage_type: Type of storage ('sqlite' or 'json')
        **kwargs: Additional arguments for the adapter

    Returns:
        StorageAdapter instance
    """
    global _default_adapter

    if _default_adapter is None:
        _default_adapter = StorageFactory.create_adapter(storage_type, **kwargs)

    return _default_adapter
