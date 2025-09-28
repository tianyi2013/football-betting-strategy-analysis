"""
Home-Away betting strategy: Bet on home team to win all games
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from .base_strategy import BaseBettingStrategy
from analytics.performance_metrics import PerformanceMetrics

class HomeAwayStrategy(BaseBettingStrategy):
    """
    Betting strategy that bets on the home team to win all games.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the home-away strategy.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        super().__init__(data_directory)
    
    def analyze_betting_performance(self, target_season: int, 
                                  odds_provider: str = "bet365") -> Dict:
        """
        Analyze betting performance for a specific season using home-away strategy.
        
        Args:
            target_season (int): Season to analyze betting performance
            odds_provider (str): Odds provider to use
            
        Returns:
            Dict: Betting performance analysis
        """
        try:
            # Load target season data
            df_target = self.load_season_data(target_season)
            
            if df_target.empty:
                return {
                    'error': f'No data available for season {target_season}',
                    'target_season': target_season
                }
            
            # Get the appropriate odds columns for this season
            home_odds_col, draw_odds_col, away_odds_col = self.get_odds_columns(target_season, odds_provider)
            
            # Check if odds columns exist in the data
            missing_odds = []
            for col in [home_odds_col, draw_odds_col, away_odds_col]:
                if col not in df_target.columns:
                    missing_odds.append(col)
            
            if missing_odds:
                return {
                    'error': f'Missing odds columns for season {target_season}: {missing_odds}',
                    'target_season': target_season
                }
            
            # Create betting records
            bet_details = []
            
            for _, match in df_target.iterrows():
                # Skip matches with missing data
                if pd.isna(match['HomeTeam']) or pd.isna(match['AwayTeam']) or \
                   pd.isna(match['FTR']):
                    continue
                
                home_team = match['HomeTeam']
                away_team = match['AwayTeam']
                result = match['FTR']
                
                # Skip if odds data is missing
                if pd.isna(match[home_odds_col]):
                    continue
                
                # Bet on home team to win
                stake = 1.0
                odds = match[home_odds_col]
                
                if not pd.isna(odds) and odds > 0:
                    bet_wins = result == 'H'
                    winnings = stake * odds if bet_wins else 0
                    
                    bet_details.append({
                        'match_date': match.get('Date', 'Unknown'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'bet_team': home_team,
                        'bet_type': 'HOME_WIN',
                        'result': result,
                        'bet_wins': bet_wins,
                        'odds': odds,
                        'stake': stake,
                        'winnings': winnings
                    })
            
            if not bet_details:
                return {
                    'error': f'No valid bets found for season {target_season}',
                    'target_season': target_season
                }
            
            # Calculate performance metrics
            metrics = PerformanceMetrics.calculate_metrics(bet_details)
            
            return {
                'target_season': target_season,
                'strategy': 'Home team to win all games',
                'total_bets': len(bet_details),
                'bet_details': bet_details,
                **metrics
            }
            
        except Exception as e:
            return {
                'error': f'Error analyzing season {target_season}: {str(e)}',
                'target_season': target_season
            }
    
    def backtest_strategy(self, start_season: int = None, 
                         end_season: int = None, 
                         odds_provider: str = "bet365") -> Dict:
        """
        Backtest the home-away strategy across multiple seasons.
        
        Args:
            start_season (int, optional): Starting season for backtest
            end_season (int, optional): Ending season for backtest
            odds_provider (str): Odds provider to use
            
        Returns:
            Dict: Comprehensive backtest results
        """
        # Determine test seasons
        if start_season is None:
            start_season = min(self.available_seasons)
        if end_season is None:
            end_season = max(self.available_seasons)
        
        test_seasons = [s for s in self.available_seasons if start_season <= s <= end_season]
        
        if not test_seasons:
            return {
                'error': f'No seasons available in range {start_season}-{end_season}',
                'start_season': start_season,
                'end_season': end_season
            }
        
        print(f"Backtesting Home-Away strategy from {start_season} to {end_season}")
        print(f"Using {odds_provider} odds")
        
        # Run analysis for each season
        season_results = []
        
        for season in test_seasons:
            result = self.analyze_betting_performance(
                season, odds_provider=odds_provider
            )
            
            if 'error' not in result:
                season_results.append(result)
        
        # Calculate overall performance
        if not season_results:
            return {
                'error': 'No successful season analyses completed',
                'start_season': start_season,
                'end_season': end_season
            }
        
        # Aggregate all bets across seasons
        all_bets = []
        for result in season_results:
            all_bets.extend(result['bet_details'])
        
        # Calculate overall metrics
        overall_metrics = PerformanceMetrics.calculate_metrics(all_bets)
        
        return {
            'strategy': 'Home team to win all games',
            'start_season': start_season,
            'end_season': end_season,
            'test_seasons': test_seasons,
            'season_results': season_results,
            'total_seasons': len(season_results),
            'bet_details': all_bets,
            'overall': overall_metrics
        }