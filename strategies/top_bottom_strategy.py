"""
Top-Bottom betting strategy: FOR top N teams + AGAINST bottom N teams
"""

from typing import Dict

import pandas as pd

from analytics.performance_metrics import PerformanceMetrics

from .base_strategy import BaseBettingStrategy


class TopBottomStrategy(BaseBettingStrategy):
    """
    Betting strategy that bets FOR top N teams and AGAINST bottom N teams.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the top-bottom strategy.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        super().__init__(data_directory)
    
    def analyze_betting_performance(self, target_season: int, top_n: int, 
                                  previous_season: int = None, 
                                  include_against_bottom: bool = True,
                                  odds_provider: str = "bet365") -> Dict:
        """
        Analyze betting performance for a specific season using top N teams from previous season.
        
        Args:
            target_season (int): Season to analyze betting performance
            top_n (int): Number of top teams to bet on
            previous_season (int, optional): Previous season to select teams from. 
                                           If None, uses target_season - 1
            include_against_bottom (bool): Whether to include betting against bottom teams
            
        Returns:
            Dict: Betting performance analysis
        """
        if previous_season is None:
            previous_season = target_season - 1
        
        # Get top N teams from previous season
        try:
            top_teams = self.analytics.get_top_teams(previous_season, top_n)
        except FileNotFoundError:
            return {
                'error': f"Previous season {previous_season} data not found",
                'target_season': target_season,
                'previous_season': previous_season,
                'top_n': top_n
            }
        
        # Get bottom N teams from previous season (excluding relegated teams)
        bottom_teams = []
        if include_against_bottom:
            try:
                bottom_teams = self.analytics.get_bottom_teams(previous_season, top_n)
            except FileNotFoundError:
                return {
                    'error': f"Previous season {previous_season} data not found for bottom teams",
                    'target_season': target_season,
                    'previous_season': previous_season,
                    'top_n': top_n
                }
        
        # Get target season data
        try:
            df_target = self.load_season_data(target_season)
        except FileNotFoundError:
            return {
                'error': f"Target season {target_season} data not found",
                'target_season': target_season,
                'previous_season': previous_season,
                'top_n': top_n
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
                'error': f"Missing odds columns for season {target_season}: {missing_odds}",
                'target_season': target_season,
                'previous_season': previous_season,
                'top_n': top_n
            }
        
        # Analyze betting performance
        bet_details = []
        
        for _, match in df_target.iterrows():
            # Skip rows with missing essential data
            if pd.isna(match['HomeTeam']) or pd.isna(match['AwayTeam']) or \
               pd.isna(match['FTR']):
                continue
                
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            result = match['FTR']
            
            # Skip if odds data is missing
            if pd.isna(match[home_odds_col]) or pd.isna(match[away_odds_col]):
                continue
            
            # Check if any of our top teams are playing (bet FOR them)
            top_teams_playing = [team for team in [home_team, away_team] if team in top_teams]
            
            # Check if any of our bottom teams are playing (bet AGAINST them)
            bottom_teams_playing = [team for team in [home_team, away_team] if team in bottom_teams]
            
            # Determine the betting strategy based on which teams are playing
            # Priority: Top vs Bottom > Top vs Top > Bottom vs Bottom > Top vs Other > Bottom vs Other
            
            if (home_team in top_teams and away_team in bottom_teams) or \
               (away_team in top_teams and home_team in bottom_teams):
                # Case 1: Top team vs Bottom team - only bet FOR the top team
                for team in top_teams_playing:
                    stake = 1  # 1 unit stake per bet
                    
                    # Get the odds for this team
                    if team == home_team:
                        odds = match[home_odds_col]
                    else:
                        odds = match[away_odds_col]
                    
                    # Skip if odds are invalid
                    if pd.isna(odds) or odds <= 0:
                        continue
                    
                    # Determine if bet wins
                    bet_wins = False
                    if team == home_team and result == 'H':
                        bet_wins = True
                    elif team == away_team and result == 'A':
                        bet_wins = True
                    
                    winnings = stake * odds if bet_wins else 0
                    
                    bet_details.append({
                        'match_date': match.get('Date', 'Unknown'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'bet_team': team,
                        'bet_type': 'FOR',
                        'result': result,
                        'bet_wins': bet_wins,
                        'odds': odds,
                        'stake': stake,
                        'winnings': winnings
                    })
            elif home_team in top_teams and away_team in top_teams:
                # Case 2: Top team vs Top team - bet FOR the higher ranked team
                # Get the ranking positions from previous season
                home_rank = top_teams.index(home_team) + 1  # 1-based ranking
                away_rank = top_teams.index(away_team) + 1  # 1-based ranking
                
                # Bet on the higher ranked team (lower rank number = higher position)
                higher_ranked_team = home_team if home_rank < away_rank else away_team
                
                stake = 1  # 1 unit stake per bet
                
                # Get the odds for the higher ranked team
                if higher_ranked_team == home_team:
                    odds = match[home_odds_col]
                else:
                    odds = match[away_odds_col]
                
                # Skip if odds are invalid
                if pd.isna(odds) or odds <= 0:
                    continue
                
                # Determine if bet wins
                bet_wins = False
                if higher_ranked_team == home_team and result == 'H':
                    bet_wins = True
                elif higher_ranked_team == away_team and result == 'A':
                    bet_wins = True
                
                winnings = stake * odds if bet_wins else 0
                
                bet_details.append({
                    'match_date': match.get('Date', 'Unknown'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'bet_team': higher_ranked_team,
                    'bet_type': 'FOR',
                    'result': result,
                    'bet_wins': bet_wins,
                    'odds': odds,
                    'stake': stake,
                    'winnings': winnings
                })
            elif home_team in bottom_teams and away_team in bottom_teams:
                # Case 3: Bottom team vs Bottom team - bet AGAINST the higher ranked team
                # Get the ranking positions from previous season (higher rank number = lower position)
                home_rank = bottom_teams.index(home_team) + 1  # 1-based ranking
                away_rank = bottom_teams.index(away_team) + 1  # 1-based ranking
                
                # Bet against the higher ranked team (lower rank number = higher position)
                higher_ranked_team = home_team if home_rank < away_rank else away_team
                
                stake = 1  # 1 unit stake per bet
                
                # Get the odds for the OPPONENT of the higher ranked team
                if higher_ranked_team == home_team:
                    # Bet on away team to win or draw
                    opponent_odds = match[away_odds_col]
                    draw_odds = match[draw_odds_col]
                else:
                    # Bet on home team to win or draw
                    opponent_odds = match[home_odds_col]
                    draw_odds = match[draw_odds_col]
                
                # Skip if odds are invalid
                if pd.isna(opponent_odds) or pd.isna(draw_odds) or opponent_odds <= 0 or draw_odds <= 0:
                    continue
                
                # Determine if bet wins (higher ranked team loses or draws)
                bet_wins = False
                if higher_ranked_team == home_team and result in ['A', 'D']:  # Away win or draw
                    bet_wins = True
                elif higher_ranked_team == away_team and result in ['H', 'D']:  # Home win or draw
                    bet_wins = True
                
                if bet_wins:
                    # Use the better odds between opponent win and draw
                    best_odds = max(opponent_odds, draw_odds)
                    winnings = stake * best_odds
                else:
                    winnings = 0
                
                bet_details.append({
                    'match_date': match.get('Date', 'Unknown'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'bet_team': higher_ranked_team,
                    'bet_type': 'AGAINST',
                    'result': result,
                    'bet_wins': bet_wins,
                    'odds': max(opponent_odds, draw_odds),
                    'stake': stake,
                    'winnings': winnings
                })
            else:
                # Case 4: Normal case - bet FOR top teams and AGAINST bottom teams separately
                
                # Bet FOR top teams
                if top_teams_playing:
                    for team in top_teams_playing:
                        stake = 1  # 1 unit stake per bet
                        
                        # Get the odds for this team
                        if team == home_team:
                            odds = match[home_odds_col]
                        else:
                            odds = match[away_odds_col]
                        
                        # Skip if odds are invalid
                        if pd.isna(odds) or odds <= 0:
                            continue
                        
                        # Determine if bet wins
                        bet_wins = False
                        if team == home_team and result == 'H':
                            bet_wins = True
                        elif team == away_team and result == 'A':
                            bet_wins = True
                        
                        winnings = stake * odds if bet_wins else 0
                        
                        bet_details.append({
                            'match_date': match.get('Date', 'Unknown'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'bet_team': team,
                            'bet_type': 'FOR',
                            'result': result,
                            'bet_wins': bet_wins,
                            'odds': odds,
                            'stake': stake,
                            'winnings': winnings
                        })
                
                # Bet AGAINST bottom teams
                if bottom_teams_playing:
                    for team in bottom_teams_playing:
                        stake = 1  # 1 unit stake per bet
                        
                        # Get the odds for the OPPONENT of this team
                        if team == home_team:
                            # Bet on away team to win or draw
                            opponent_odds = match[away_odds_col]
                            draw_odds = match[draw_odds_col]
                        else:
                            # Bet on home team to win or draw
                            opponent_odds = match[home_odds_col]
                            draw_odds = match[draw_odds_col]
                        
                        # Skip if odds are invalid
                        if pd.isna(opponent_odds) or pd.isna(draw_odds) or opponent_odds <= 0 or draw_odds <= 0:
                            continue
                        
                        # Determine if bet wins (team loses or draws)
                        bet_wins = False
                        if team == home_team and result in ['A', 'D']:  # Away win or draw
                            bet_wins = True
                        elif team == away_team and result in ['H', 'D']:  # Home win or draw
                            bet_wins = True
                        
                        if bet_wins:
                            # Use the better odds between opponent win and draw
                            best_odds = max(opponent_odds, draw_odds)
                            winnings = stake * best_odds
                        else:
                            winnings = 0
                        
                        bet_details.append({
                            'match_date': match.get('Date', 'Unknown'),
                            'home_team': home_team,
                            'away_team': away_team,
                            'bet_team': team,
                            'bet_type': 'AGAINST',
                            'result': result,
                            'bet_wins': bet_wins,
                            'odds': max(opponent_odds, draw_odds),
                            'stake': stake,
                            'winnings': winnings
                        })
        
        # Calculate performance metrics
        metrics = PerformanceMetrics.calculate_metrics(bet_details)
        
        return {
            'target_season': target_season,
            'previous_season': previous_season,
            'top_n': top_n,
            'top_teams': top_teams,
            'bottom_teams': bottom_teams,
            'bet_details': bet_details,
            **metrics
        }
    
    def backtest_strategy(self, top_n: int, start_season: int = None, 
                         end_season: int = None, include_against_bottom: bool = True,
                         odds_provider: str = "bet365") -> Dict:
        """
        Backtest the betting strategy across multiple seasons.
        
        Args:
            top_n (int): Number of top teams to bet on
            start_season (int, optional): Starting season for backtest
            end_season (int, optional): Ending season for backtest
            include_against_bottom (bool): Whether to include betting against bottom teams
            
        Returns:
            Dict: Comprehensive backtest results
        """
        if start_season is None:
            start_season = min(self.available_seasons) + 1  # Need previous season data
        if end_season is None:
            end_season = max(self.available_seasons)
        
        # Get seasons to test
        test_seasons = [s for s in self.available_seasons 
                       if start_season <= s <= end_season and s > min(self.available_seasons)]
        
        if not test_seasons:
            return {'error': 'No valid seasons found for backtesting'}
        
        # Run analysis for each season
        season_results = []
        
        for season in test_seasons:
            result = self.analyze_betting_performance(
                season, top_n, include_against_bottom=include_against_bottom,
                odds_provider=odds_provider
            )
            
            if 'error' not in result:
                season_results.append(result)
        
        # Calculate overall performance
        overall_stats = PerformanceMetrics.calculate_overall_statistics(season_results)
        
        return {
            'strategy': f"Top {top_n} teams FOR + Bottom {top_n} teams AGAINST" if include_against_bottom else f"Top {top_n} teams FOR only",
            'top_n': top_n,
            'test_period': f"{min(test_seasons)}-{max(test_seasons)}",
            'seasons_tested': len(season_results),
            'season_results': season_results,
            **overall_stats
        }
