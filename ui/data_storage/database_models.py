#!/usr/bin/env python3
"""
Database models for betting data storage.
Provides ORM-like interface using SQLite with better data integrity and querying capabilities.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import sqlite3
import os
from pathlib import Path


class DatabaseManager:
    """Manages database connections and schema initialization"""

    def __init__(self, db_path: str = 'betting_data.db'):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _init_db(self):
        """Initialize database schema if it doesn't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Bets table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    placement_date TIMESTAMP NOT NULL,
                    match_date DATE NOT NULL,
                    league TEXT NOT NULL,
                    game TEXT NOT NULL,
                    bet_team TEXT NOT NULL,
                    bet_type TEXT NOT NULL DEFAULT 'WIN',
                    stake REAL NOT NULL,
                    odds REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    profit REAL DEFAULT 0,
                    strategy TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT,
                    supporting_strategies TEXT,
                    individual_strategies TEXT,
                    strategy_priority INTEGER,
                    round_number INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(placement_date, game, bet_team)
                )
            ''')

            # Create index on frequently queried columns
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_bets_match_date ON bets(match_date)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_bets_league ON bets(league)
            ''')


            conn.commit()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute('PRAGMA foreign_keys = ON')
        return conn


class BetRepository:
    """Repository pattern for bet data access"""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize bet repository.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def add_bet(self, bet_data: Dict[str, Any]) -> int:
        """
        Add a new bet to the database.

        Args:
            bet_data: Dictionary containing bet information.
                     Supports both flat structure and nested 'opportunity' structure.

        Returns:
            Inserted bet ID
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # Support both flat structure and nested 'opportunity' structure
            opportunity = bet_data.get('opportunity', {})
            league = bet_data.get('league') or opportunity.get('league')
            game = bet_data.get('game') or opportunity.get('game')
            bet_team = bet_data.get('bet_team') or opportunity.get('bet_team')
            strategy = bet_data.get('strategy') or opportunity.get('strategy')
            confidence = bet_data.get('confidence') or opportunity.get('confidence')
            reason = bet_data.get('reason') or opportunity.get('reason')
            supporting_strategies = bet_data.get('supporting_strategies') or opportunity.get('supporting_strategies', [])
            individual_strategies = bet_data.get('individual_strategies') or opportunity.get('individual_strategies', {})
            strategy_priority = bet_data.get('strategy_priority') or opportunity.get('strategy_priority')
            round_number = bet_data.get('round_number') or opportunity.get('round_number')

            cursor.execute('''
                INSERT INTO bets (
                    placement_date, match_date, league, game, bet_team,
                    bet_type, stake, odds, status, strategy, confidence,
                    reason, supporting_strategies, individual_strategies,
                    strategy_priority, round_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bet_data.get('placement_date', bet_data.get('date', datetime.now().isoformat())),
                bet_data.get('match_date') or opportunity.get('match_date'),
                league,
                game,
                bet_team,
                bet_data.get('bet_type', 'WIN'),
                bet_data.get('stake'),
                bet_data.get('odds'),
                bet_data.get('status', 'pending'),
                strategy,
                confidence,
                reason,
                json.dumps(supporting_strategies) if supporting_strategies else None,
                json.dumps(individual_strategies) if individual_strategies else None,
                strategy_priority,
                round_number
            ))

            conn.commit()
            return cursor.lastrowid

    def get_all_bets(self, include_processed: bool = False) -> List[Dict[str, Any]]:
        """
        Get all bets from the database.

        Args:
            include_processed: Include processed bets

        Returns:
            List of bet dictionaries
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM bets ORDER BY created_at DESC
            ''')
            return self._rows_to_dicts(cursor.fetchall())

    def get_bets_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get bets filtered by status"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM bets WHERE status = ? ORDER BY created_at DESC
            ''', (status,))
            return self._rows_to_dicts(cursor.fetchall())

    def get_bets_by_league(self, league: str) -> List[Dict[str, Any]]:
        """Get bets filtered by league"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM bets WHERE league = ? ORDER BY created_at DESC
            ''', (league,))
            return self._rows_to_dicts(cursor.fetchall())

    def get_bets_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get bets within a date range (match_date)"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM bets 
                WHERE match_date BETWEEN ? AND ?
                ORDER BY match_date DESC
            ''', (start_date, end_date))
            return self._rows_to_dicts(cursor.fetchall())

    def update_bet(self, bet_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing bet.

        Args:
            bet_id: ID of bet to update
            update_data: Dictionary of fields to update

        Returns:
            True if update was successful
        """
        if not update_data:
            return False

        # Build dynamic update query
        allowed_fields = {
            'status', 'profit', 'odds', 'stake', 'reason'
        }
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        if not update_data:
            return False

        update_data['updated_at'] = datetime.now().isoformat()

        set_clause = ', '.join([f'{k} = ?' for k in update_data.keys()])
        values = list(update_data.values()) + [bet_id]

        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE bets SET {set_clause} WHERE id = ?
            ''', values)
            conn.commit()
            return cursor.rowcount > 0

    def delete_bet(self, bet_id: int) -> bool:
        """Delete a bet by ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bets WHERE id = ?', (bet_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_bet_by_id(self, bet_id: int) -> Optional[Dict[str, Any]]:
        """Get a single bet by ID"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bets WHERE id = ?', (bet_id,))
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def replace_all_bets(self, bets_list: List[Dict[str, Any]]) -> bool:
        """
        Replace all bets with new list (for migration from JSON).

        Args:
            bets_list: List of bet dictionaries

        Returns:
            True if successful
        """
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            # Clear existing bets
            cursor.execute('DELETE FROM bets')

            # Insert new bets
            for bet in bets_list:
                status = bet.get('status', 'pending')
                stake = float(bet.get('stake', 0))
                odds = float(bet.get('odds', 0))

                # Calculate profit based on status
                if status == 'won':
                    profit = (stake * odds) - stake
                elif status == 'lost':
                    profit = -stake
                else:  # pending or unknown
                    profit = 0

                cursor.execute('''
                    INSERT INTO bets (
                        created_at, placement_date, match_date, league, game, bet_team,
                        bet_type, stake, odds, status, profit, strategy, confidence,
                        reason, supporting_strategies, individual_strategies,
                        strategy_priority, round_number
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    bet.get('created_at', datetime.now().isoformat()),
                    bet.get('placement_date', bet.get('date')),
                    bet.get('match_date'),
                    bet.get('opportunity', {}).get('league', 'Unknown'),
                    bet.get('opportunity', {}).get('game', 'Unknown'),
                    bet.get('opportunity', {}).get('bet_team'),
                    bet.get('bet_type', 'WIN'),
                    stake,
                    odds,
                    status,
                    profit,
                    bet.get('opportunity', {}).get('strategy'),
                    bet.get('opportunity', {}).get('confidence'),
                    bet.get('opportunity', {}).get('reason'),
                    json.dumps(bet.get('opportunity', {}).get('supporting_strategies', [])),
                    json.dumps(bet.get('opportunity', {}).get('individual_strategies', {})),
                    bet.get('opportunity', {}).get('strategy_priority'),
                    bet.get('opportunity', {}).get('round_number')
                ))

            conn.commit()
            return True

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary with parsed JSON fields"""
        if not row:
            return None

        data = dict(row)
        # Parse JSON fields
        if data.get('supporting_strategies'):
            data['supporting_strategies'] = json.loads(data['supporting_strategies'])
        if data.get('individual_strategies'):
            data['individual_strategies'] = json.loads(data['individual_strategies'])

        return data

    def _rows_to_dicts(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
        """Convert list of sqlite3.Row to list of dictionaries"""
        return [self._row_to_dict(row) for row in rows]



