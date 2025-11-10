"""
Form-based betting strategy: Bet on teams based on recent form (last N games)
"""

from typing import Dict

import pandas as pd

from analytics.performance_metrics import PerformanceMetrics

from .base_strategy import BaseBettingStrategy


class FormStrategy(BaseBettingStrategy):
    """
    Betting strategy that bets on teams based on their recent form.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the form-based strategy.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        super().__init__(data_directory)
    
    def calculate_team_form(self, team: str, season: int, match_date: str, 
                           form_games: int = 5) -> Dict:
        """
        Calculate team form based on last N games before the given match date.
        
        Args:
            team (str): Team name
            season (int): Season year
            match_date (str): Match date to calculate form up to
            form_games (int): Number of recent games to consider for form
            
        Returns:
            Dict: Form statistics including wins, draws, losses, points, form_score
        """
        try:
            # Load season data
            df = self.load_season_data(season)
            
            # Convert date column to datetime - now standardized to YYYY-MM-DD format
            df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d', errors='coerce')
            
            # Parse match_date - now standardized to YYYY-MM-DD format
            match_date_dt = pd.to_datetime(match_date, format='%Y-%m-%d', errors='coerce')
            
            if pd.isna(match_date_dt):
                return {'error': f'Invalid date format: {match_date}'}
            
            # Filter matches for this team before the match date
            team_matches = df[
                ((df['HomeTeam'] == team) | (df['AwayTeam'] == team)) &
                (df['Date'] < match_date_dt)
            ].copy()
            
            if team_matches.empty:
                return {
                    'games_played': 0,
                    'wins': 0,
                    'draws': 0,
                    'losses': 0,
                    'points': 0,
                    'form_score': 0.0,
                    'form_games': form_games
                }
            
            # Sort by date to get most recent games
            team_matches = team_matches.sort_values('Date', ascending=False)
            
            # Take only the last N games
            recent_matches = team_matches.head(form_games)
            
            # Calculate form statistics
            wins = 0
            draws = 0
            losses = 0
            
            for _, match in recent_matches.iterrows():
                if match['HomeTeam'] == team:
                    # Team is home
                    if match['FTR'] == 'H':
                        wins += 1
                    elif match['FTR'] == 'D':
                        draws += 1
                    else:
                        losses += 1
                else:
                    # Team is away
                    if match['FTR'] == 'A':
                        wins += 1
                    elif match['FTR'] == 'D':
                        draws += 1
                    else:
                        losses += 1
            
            points = wins * 3 + draws
            form_score = points / (form_games * 3) if form_games > 0 else 0.0
            
            return {
                'games_played': len(recent_matches),
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'points': points,
                'form_score': form_score,
                'form_games': form_games
            }
            
        except Exception as e:
            return {'error': f'Error calculating form for {team}: {str(e)}'}
    
    def get_form_thresholds(self, form_games: int = 5) -> Dict:
        """
        Get form thresholds for betting decisions.
        
        Args:
            form_games (int): Number of games to consider for form
            
        Returns:
            Dict: Form thresholds for betting decisions
        """
        return {
            'excellent_form': 0.8,  # 80% of maximum points
            'good_form': 0.6,       # 60% of maximum points
            'poor_form': 0.3,       # 30% of maximum points
            'terrible_form': 0.2    # 20% of maximum points
        }
    
    def analyze_betting_performance(self, target_season: int, form_games: int = 5,
                                  form_threshold: float = 0.6,
                                  bet_against_poor_form: bool = True,
                                  odds_provider: str = "bet365") -> Dict:
        """
        Analyze betting performance for a specific season using form-based strategy.
        
        Args:
            target_season (int): Season to analyze betting performance
            form_games (int): Number of recent games to consider for form
            form_threshold (float): Minimum form score to bet on team
            bet_against_poor_form (bool): Whether to bet against teams with poor form
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
            
            # Get form thresholds
            thresholds = self.get_form_thresholds(form_games)
            
            # Create betting records
            bet_details = []
            
            # Convert date column to datetime for proper processing
            df_target['Date'] = pd.to_datetime(df_target['Date'], format='%Y-%m-%d', errors='coerce')
            
            for _, match in df_target.iterrows():
                # Skip matches with missing data
                if pd.isna(match['HomeTeam']) or pd.isna(match['AwayTeam']) or \
                   pd.isna(match['FTR']) or pd.isna(match['Date']):
                    continue
                
                home_team = match['HomeTeam']
                away_team = match['AwayTeam']
                match_date = match['Date']
                result = match['FTR']
                
                # Skip if odds data is missing
                if pd.isna(match[home_odds_col]) or pd.isna(match[away_odds_col]):
                    continue
                
                # Calculate form for both teams
                # Convert datetime to string format expected by calculate_team_form (now YYYY-MM-DD)
                match_date_str = match_date.strftime('%Y-%m-%d')
                home_form = self.calculate_team_form(home_team, target_season, match_date_str, form_games)
                away_form = self.calculate_team_form(away_team, target_season, match_date_str, form_games)
                
                # Skip if we can't calculate form (insufficient games)
                if 'error' in home_form or 'error' in away_form:
                    continue
                
                if home_form['games_played'] < form_games or away_form['games_played'] < form_games:
                    continue
                
                # Determine betting strategy based on form
                home_form_score = home_form['form_score']
                away_form_score = away_form['form_score']
                
                # Bet on teams with good form
                if home_form_score >= form_threshold:
                    # Bet on home team
                    stake = 1.0
                    odds = match[home_odds_col]
                    
                    if not pd.isna(odds) and odds > 0:
                        bet_wins = result == 'H'
                        winnings = stake * odds if bet_wins else 0
                        
                        bet_details.append({
                            'match_date': match_date,
                            'home_team': home_team,
                            'away_team': away_team,
                            'bet_team': home_team,
                            'bet_type': 'FORM_GOOD',
                            'result': result,
                            'bet_wins': bet_wins,
                            'odds': odds,
                            'stake': stake,
                            'winnings': winnings,
                            'form_score': home_form_score,
                            'opponent_form_score': away_form_score
                        })
                
                if away_form_score >= form_threshold:
                    # Bet on away team
                    stake = 1.0
                    odds = match[away_odds_col]
                    
                    if not pd.isna(odds) and odds > 0:
                        bet_wins = result == 'A'
                        winnings = stake * odds if bet_wins else 0
                        
                        bet_details.append({
                            'match_date': match_date,
                            'home_team': home_team,
                            'away_team': away_team,
                            'bet_team': away_team,
                            'bet_type': 'FORM_GOOD',
                            'result': result,
                            'bet_wins': bet_wins,
                            'odds': odds,
                            'stake': stake,
                            'winnings': winnings,
                            'form_score': away_form_score,
                            'opponent_form_score': home_form_score
                        })
                
                # Bet against teams with poor form (if enabled)
                if bet_against_poor_form:
                    poor_form_threshold = thresholds['poor_form']
                    
                    if home_form_score <= poor_form_threshold:
                        # Bet against home team (bet on away team or draw)
                        stake = 1.0
                        away_odds = match[away_odds_col]
                        draw_odds = match[draw_odds_col]
                        
                        if not pd.isna(away_odds) and not pd.isna(draw_odds) and away_odds > 0 and draw_odds > 0:
                            bet_wins = result in ['A', 'D']
                            best_odds = max(away_odds, draw_odds)
                            winnings = stake * best_odds if bet_wins else 0
                            
                            bet_details.append({
                                'match_date': match_date,
                                'home_team': home_team,
                                'away_team': away_team,
                                'bet_team': home_team,
                                'bet_type': 'FORM_POOR_AGAINST',
                                'result': result,
                                'bet_wins': bet_wins,
                                'odds': best_odds,
                                'stake': stake,
                                'winnings': winnings,
                                'form_score': home_form_score,
                                'opponent_form_score': away_form_score
                            })
                    
                    if away_form_score <= poor_form_threshold:
                        # Bet against away team (bet on home team or draw)
                        stake = 1.0
                        home_odds = match[home_odds_col]
                        draw_odds = match[draw_odds_col]
                        
                        if not pd.isna(home_odds) and not pd.isna(draw_odds) and home_odds > 0 and draw_odds > 0:
                            bet_wins = result in ['H', 'D']
                            best_odds = max(home_odds, draw_odds)
                            winnings = stake * best_odds if bet_wins else 0
                            
                            bet_details.append({
                                'match_date': match_date,
                                'home_team': home_team,
                                'away_team': away_team,
                                'bet_team': away_team,
                                'bet_type': 'FORM_POOR_AGAINST',
                                'result': result,
                                'bet_wins': bet_wins,
                                'odds': best_odds,
                                'stake': stake,
                                'winnings': winnings,
                                'form_score': away_form_score,
                                'opponent_form_score': home_form_score
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
                'strategy': f'Form-based (last {form_games} games, threshold {form_threshold})',
                'form_games': form_games,
                'form_threshold': form_threshold,
                'bet_against_poor_form': bet_against_poor_form,
                'total_bets': len(bet_details),
                'bet_details': bet_details,
                **metrics
            }
            
        except Exception as e:
            return {
                'error': f'Error analyzing season {target_season}: {str(e)}',
                'target_season': target_season
            }
    
    def backtest_strategy(self, form_games: int = 5, form_threshold: float = 0.6,
                         bet_against_poor_form: bool = True, start_season: int = None,
                         end_season: int = None, odds_provider: str = "bet365") -> Dict:
        """
        Backtest the form-based strategy across multiple seasons.
        
        Args:
            form_games (int): Number of recent games to consider for form
            form_threshold (float): Minimum form score to bet on team
            bet_against_poor_form (bool): Whether to bet against teams with poor form
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
        
        print(f"Backtesting Form-based strategy from {start_season} to {end_season}")
        print(f"Form games: {form_games}, Threshold: {form_threshold}")
        print(f"Bet against poor form: {bet_against_poor_form}")
        print(f"Using {odds_provider} odds")
        
        # Run analysis for each season
        season_results = []
        
        for season in test_seasons:
            result = self.analyze_betting_performance(
                season, form_games=form_games, form_threshold=form_threshold,
                bet_against_poor_form=bet_against_poor_form, odds_provider=odds_provider
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
            'strategy': f'Form-based (last {form_games} games, threshold {form_threshold})',
            'form_games': form_games,
            'form_threshold': form_threshold,
            'bet_against_poor_form': bet_against_poor_form,
            'start_season': start_season,
            'end_season': end_season,
            'test_seasons': test_seasons,
            'season_results': season_results,
            'total_seasons': len(season_results),
            'bet_details': all_bets,
            'overall': overall_metrics
        }
