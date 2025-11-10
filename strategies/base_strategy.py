"""
Base betting strategy class
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Tuple

import pandas as pd

from analytics.league_analytics import PremierLeagueAnalytics


class BaseBettingStrategy(ABC):
    """
    Abstract base class for betting strategies.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the strategy with data directory.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        self.data_directory = data_directory
        self.analytics = PremierLeagueAnalytics(data_directory)
        self.available_seasons = self.analytics.available_seasons
    
    def get_odds_columns(self, season_year: int, odds_provider: str = "bet365") -> Tuple[str, str, str]:
        """
        Get the appropriate odds column names based on season year and provider.
        Uses closing odds for more accurate market prices when available.
        
        Args:
            season_year (int): Season year
            odds_provider (str): Odds provider ("bet365", "pinnacle", "william_hill", etc.)
            
        Returns:
            Tuple[str, str, str]: (home_odds_col, draw_odds_col, away_odds_col)
        """
        if season_year <= 2001:
            # Use Ladbrokes odds for 2000-2001 (no closing odds available)
            return 'LBH', 'LBD', 'LBA'
        elif season_year <= 2018:
            # Use Bet365 pre-closing odds for 2002-2018 (no closing odds available)
            return 'B365H', 'B365D', 'B365A'
        else:
            # Use closing odds for 2019+ (more accurate market prices)
            if odds_provider.lower() == "bet365":
                return 'B365CH', 'B365CD', 'B365CA'
            elif odds_provider.lower() == "pinnacle":
                return 'PSCH', 'PSCD', 'PSCA'
            elif odds_provider.lower() == "william_hill":
                return 'WHCH', 'WHCD', 'WHCA'
            elif odds_provider.lower() == "vc_bet":
                return 'VCCH', 'VCCD', 'VCCA'
            elif odds_provider.lower() == "1xbet":
                return '1XBCH', '1XBCD', '1XBCA'
            else:
                # Default to Bet365 closing odds
                return 'B365CH', 'B365CD', 'B365CA'
    
    def load_season_data(self, season_year: int) -> pd.DataFrame:
        """
        Load season data with error handling.
        
        Args:
            season_year (int): Season year
            
        Returns:
            pd.DataFrame: Season data
        """
        file_path = os.path.join(self.data_directory, f"{season_year}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Season {season_year} data not found")
        
        return pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')
    
    @abstractmethod
    def analyze_betting_performance(self, target_season: int, **kwargs) -> Dict:
        """
        Analyze betting performance for a specific season.
        
        Args:
            target_season (int): Season to analyze betting performance
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dict: Betting performance analysis
        """
        pass
    
    @abstractmethod
    def backtest_strategy(self, **kwargs) -> Dict:
        """
        Backtest the betting strategy across multiple seasons.
        
        Args:
            **kwargs: Strategy-specific parameters
            
        Returns:
            Dict: Comprehensive backtest results
        """
        pass
