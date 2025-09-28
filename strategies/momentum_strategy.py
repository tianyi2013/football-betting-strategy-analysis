"""
Momentum-based betting strategy: Bet on teams with winning streaks and against teams with losing streaks
"""

from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from .base_strategy import BaseBettingStrategy
from analytics.performance_metrics import PerformanceMetrics

class MomentumStrategy(BaseBettingStrategy):
    """
    Betting strategy that bets on teams with momentum (consecutive wins/losses).
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the momentum-based strategy.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        super().__init__(data_directory)
    
    def calculate_team_momentum(self, team: str, season: int, match_date: str, 
                               lookback_games: int = 10) -> Dict:
        """
        Calculate team momentum based on recent consecutive wins/losses.
        
        Args:
            team (str): Team name
            season (int): Season year
            match_date (str): Match date to calculate momentum up to
            lookback_games (int): Number of recent games to look back for momentum
            
        Returns:
            Dict: Momentum statistics including current streak, momentum score, etc.
        """
        try:
            # Load season data
            df = self.load_season_data(season)
            
            # Convert date column to datetime - all dates are now standardized to yyyy-mm-dd format
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
                    'current_streak': 0,
                    'streak_type': 'none',
                    'momentum_score': 0.0,
                    'lookback_games': lookback_games
                }
            
            # Sort by date to get most recent games
            team_matches = team_matches.sort_values('Date', ascending=False)
            
            # Take only the last N games
            recent_matches = team_matches.head(lookback_games)
            
            if recent_matches.empty:
                return {
                    'games_played': 0,
                    'current_streak': 0,
                    'streak_type': 'none',
                    'momentum_score': 0.0,
                    'lookback_games': lookback_games
                }
            
            # Calculate results for each match
            results = []
            for _, match in recent_matches.iterrows():
                if match['HomeTeam'] == team:
                    # Team is home
                    if match['FTR'] == 'H':
                        results.append('W')
                    elif match['FTR'] == 'D':
                        results.append('D')
                    else:
                        results.append('L')
                else:
                    # Team is away
                    if match['FTR'] == 'A':
                        results.append('W')
                    elif match['FTR'] == 'D':
                        results.append('D')
                    else:
                        results.append('L')
            
            # Calculate current streak
            current_streak = 0
            streak_type = 'none'
            
            if results:
                first_result = results[0]
                if first_result == 'W':
                    streak_type = 'winning'
                elif first_result == 'L':
                    streak_type = 'losing'
                else:
                    streak_type = 'draw'
                
                # Count consecutive results of the same type
                for result in results:
                    if result == first_result:
                        current_streak += 1
                    else:
                        break
            
            # Calculate momentum score
            # Positive for winning streaks, negative for losing streaks
            if streak_type == 'winning':
                momentum_score = current_streak / lookback_games
            elif streak_type == 'losing':
                momentum_score = -current_streak / lookback_games
            else:
                momentum_score = 0.0
            
            return {
                'games_played': len(recent_matches),
                'current_streak': current_streak,
                'streak_type': streak_type,
                'momentum_score': momentum_score,
                'lookback_games': lookback_games,
                'recent_results': results[:5]  # Last 5 results for debugging
            }
            
        except Exception as e:
            return {'error': f'Error calculating momentum for {team}: {str(e)}'}
    
    def get_momentum_thresholds(self) -> Dict:
        """
        Get momentum thresholds for betting decisions.
        
        Returns:
            Dict: Momentum thresholds for betting decisions
        """
        return {
            'strong_winning_momentum': 0.3,  # 3+ consecutive wins
            'good_winning_momentum': 0.2,    # 2+ consecutive wins
            'strong_losing_momentum': -0.3,  # 3+ consecutive losses
            'good_losing_momentum': -0.2     # 2+ consecutive losses
        }
    
    def analyze_betting_performance(self, target_season: int, lookback_games: int = 10,
                                  winning_momentum_threshold: float = 0.2,
                                  losing_momentum_threshold: float = -0.2,
                                  bet_against_losing_momentum: bool = True,
                                  odds_provider: str = "bet365",
                                  show_details: bool = False) -> Dict:
        """
        Analyze betting performance for a specific season using momentum-based strategy.
        
        Args:
            target_season (int): Season to analyze betting performance
            lookback_games (int): Number of recent games to look back for momentum
            winning_momentum_threshold (float): Minimum momentum score to bet on team
            losing_momentum_threshold (float): Maximum momentum score to bet against team
            bet_against_losing_momentum (bool): Whether to bet against teams with losing momentum
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
            
            # Get momentum thresholds
            thresholds = self.get_momentum_thresholds()
            
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
                
                # Calculate momentum for both teams
                # Convert datetime to string format expected by calculate_team_momentum (now YYYY-MM-DD)
                match_date_str = match_date.strftime('%Y-%m-%d')
                home_momentum = self.calculate_team_momentum(home_team, target_season, match_date_str, lookback_games)
                away_momentum = self.calculate_team_momentum(away_team, target_season, match_date_str, lookback_games)
                
                # Skip if we can't calculate momentum (insufficient games)
                if 'error' in home_momentum or 'error' in away_momentum:
                    continue
                
                if home_momentum['games_played'] < 2 or away_momentum['games_played'] < 2:
                    continue
                
                # Determine betting strategy based on momentum
                home_momentum_score = home_momentum['momentum_score']
                away_momentum_score = away_momentum['momentum_score']
                
                # Bet on teams with strong winning momentum
                # Avoid betting on both teams (guaranteed loss due to spread)
                if home_momentum_score >= winning_momentum_threshold and away_momentum_score >= winning_momentum_threshold:
                    # Both teams have winning momentum - check if they're equal
                    if abs(home_momentum_score - away_momentum_score) < 0.01:  # Essentially equal
                        # Bet on draw when both teams have equal momentum
                        stake = 1.0
                        odds = match[draw_odds_col]
                        
                        if not pd.isna(odds) and odds > 0:
                            bet_wins = result == 'D'
                            winnings = stake * odds if bet_wins else 0
                            
                            bet_details.append({
                                'match_date': match_date,
                                'home_team': home_team,
                                'away_team': away_team,
                                'bet_team': 'DRAW',
                                'bet_type': 'MOMENTUM_DRAW',
                                'result': result,
                                'bet_wins': bet_wins,
                                'odds': odds,
                                'stake': stake,
                                'winnings': winnings,
                                'momentum_score': (home_momentum_score + away_momentum_score) / 2,
                                'streak_type': 'equal_momentum',
                                'current_streak': 0,
                                'opponent_momentum_score': (home_momentum_score + away_momentum_score) / 2,
                                'recent_results': f"Home: {', '.join(home_momentum.get('recent_results', []))} | Away: {', '.join(away_momentum.get('recent_results', []))}",
                                'opponent_recent_results': []
                            })
                    else:
                        # Bet on the team with higher momentum
                        if home_momentum_score > away_momentum_score:
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
                                    'bet_type': 'MOMENTUM_WINNING',
                                    'result': result,
                                    'bet_wins': bet_wins,
                                    'odds': odds,
                                    'stake': stake,
                                    'winnings': winnings,
                                    'momentum_score': home_momentum_score,
                                    'streak_type': home_momentum['streak_type'],
                                    'current_streak': home_momentum['current_streak'],
                                    'opponent_momentum_score': away_momentum_score,
                                    'recent_results': home_momentum.get('recent_results', []),
                                    'opponent_recent_results': away_momentum.get('recent_results', [])
                                })
                        else:
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
                                    'bet_type': 'MOMENTUM_WINNING',
                                    'result': result,
                                    'bet_wins': bet_wins,
                                    'odds': odds,
                                    'stake': stake,
                                    'winnings': winnings,
                                    'momentum_score': away_momentum_score,
                                    'streak_type': away_momentum['streak_type'],
                                    'current_streak': away_momentum['current_streak'],
                                    'opponent_momentum_score': home_momentum_score,
                                    'recent_results': away_momentum.get('recent_results', []),
                                    'opponent_recent_results': home_momentum.get('recent_results', [])
                                })
                elif home_momentum_score >= winning_momentum_threshold:
                    # Only home team has winning momentum
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
                            'bet_type': 'MOMENTUM_WINNING',
                            'result': result,
                            'bet_wins': bet_wins,
                            'odds': odds,
                            'stake': stake,
                            'winnings': winnings,
                            'momentum_score': home_momentum_score,
                            'streak_type': home_momentum['streak_type'],
                            'current_streak': home_momentum['current_streak'],
                            'opponent_momentum_score': away_momentum_score,
                            'recent_results': home_momentum.get('recent_results', []),
                            'opponent_recent_results': away_momentum.get('recent_results', [])
                        })
                elif away_momentum_score >= winning_momentum_threshold:
                    # Only away team has winning momentum
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
                            'bet_type': 'MOMENTUM_WINNING',
                            'result': result,
                            'bet_wins': bet_wins,
                            'odds': odds,
                            'stake': stake,
                            'winnings': winnings,
                            'momentum_score': away_momentum_score,
                            'streak_type': away_momentum['streak_type'],
                            'current_streak': away_momentum['current_streak'],
                            'opponent_momentum_score': home_momentum_score,
                            'recent_results': away_momentum.get('recent_results', []),
                            'opponent_recent_results': home_momentum.get('recent_results', [])
                        })
                
                # Bet against teams with strong losing momentum (if enabled)
                if bet_against_losing_momentum:
                    if home_momentum_score <= losing_momentum_threshold:
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
                                'bet_type': 'MOMENTUM_LOSING_AGAINST',
                                'result': result,
                                'bet_wins': bet_wins,
                                'odds': best_odds,
                                'stake': stake,
                                'winnings': winnings,
                                'momentum_score': home_momentum_score,
                                'streak_type': home_momentum['streak_type'],
                                'current_streak': home_momentum['current_streak'],
                                'opponent_momentum_score': away_momentum_score,
                                'recent_results': home_momentum.get('recent_results', []),
                                'opponent_recent_results': away_momentum.get('recent_results', [])
                            })
                    
                    if away_momentum_score <= losing_momentum_threshold:
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
                                'bet_type': 'MOMENTUM_LOSING_AGAINST',
                                'result': result,
                                'bet_wins': bet_wins,
                                'odds': best_odds,
                                'stake': stake,
                                'winnings': winnings,
                                'momentum_score': away_momentum_score,
                                'streak_type': away_momentum['streak_type'],
                                'current_streak': away_momentum['current_streak'],
                                'opponent_momentum_score': home_momentum_score,
                                'recent_results': away_momentum.get('recent_results', []),
                                'opponent_recent_results': home_momentum.get('recent_results', [])
                            })
            
            if not bet_details:
                return {
                    'error': f'No valid bets found for season {target_season}',
                    'target_season': target_season
                }
            
            # Calculate performance metrics
            metrics = PerformanceMetrics.calculate_metrics(bet_details)
            
            # Print detailed bet information if requested
            if show_details:
                self._print_bet_details(bet_details, lookback_games)
            
            return {
                'target_season': target_season,
                'strategy': f'Momentum-based (lookback {lookback_games} games, winning threshold {winning_momentum_threshold})',
                'lookback_games': lookback_games,
                'winning_momentum_threshold': winning_momentum_threshold,
                'losing_momentum_threshold': losing_momentum_threshold,
                'bet_against_losing_momentum': bet_against_losing_momentum,
                'total_bets': len(bet_details),
                'bet_details': bet_details,
                **metrics
            }
            
        except Exception as e:
            return {
                'error': f'Error analyzing season {target_season}: {str(e)}',
                'target_season': target_season
            }
    
    def backtest_strategy(self, lookback_games: int = 10, winning_momentum_threshold: float = 0.2,
                         losing_momentum_threshold: float = -0.2, bet_against_losing_momentum: bool = True,
                         start_season: int = None, end_season: int = None, 
                         odds_provider: str = "bet365", show_details: bool = False) -> Dict:
        """
        Backtest the momentum-based strategy across multiple seasons.
        
        Args:
            lookback_games (int): Number of recent games to look back for momentum
            winning_momentum_threshold (float): Minimum momentum score to bet on team
            losing_momentum_threshold (float): Maximum momentum score to bet against team
            bet_against_losing_momentum (bool): Whether to bet against teams with losing momentum
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
        
        print(f"Backtesting Momentum-based strategy from {start_season} to {end_season}")
        print(f"Lookback games: {lookback_games}")
        print(f"Winning momentum threshold: {winning_momentum_threshold}")
        print(f"Losing momentum threshold: {losing_momentum_threshold}")
        print(f"Bet against losing momentum: {bet_against_losing_momentum}")
        print(f"Using {odds_provider} odds")
        
        # Run analysis for each season
        season_results = []
        
        for season in test_seasons:
            result = self.analyze_betting_performance(
                season, lookback_games=lookback_games,
                winning_momentum_threshold=winning_momentum_threshold,
                losing_momentum_threshold=losing_momentum_threshold,
                bet_against_losing_momentum=bet_against_losing_momentum,
                odds_provider=odds_provider,
                show_details=show_details
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
            'strategy': f'Momentum-based (lookback {lookback_games} games, winning threshold {winning_momentum_threshold})',
            'lookback_games': lookback_games,
            'winning_momentum_threshold': winning_momentum_threshold,
            'losing_momentum_threshold': losing_momentum_threshold,
            'bet_against_losing_momentum': bet_against_losing_momentum,
            'start_season': start_season,
            'end_season': end_season,
            'test_seasons': test_seasons,
            'season_results': season_results,
            'total_seasons': len(season_results),
            'bet_details': all_bets,
            'overall': overall_metrics
        }
    
    def _print_bet_details(self, bet_details: List[Dict], lookback_games: int) -> None:
        """
        Print detailed information about each bet and save to CSV.
        
        Args:
            bet_details (List[Dict]): List of bet details
            lookback_games (int): Number of lookback games for context
        """
        print("\n" + "="*120)
        print("DETAILED BET ANALYSIS")
        print("="*120)
        
        # Prepare data for CSV
        csv_data = []
        
        for i, bet in enumerate(bet_details, 1):
            match_date = bet['match_date'].strftime('%d/%m/%Y')
            home_team = bet['home_team']
            away_team = bet['away_team']
            bet_team = bet['bet_team']
            bet_type = bet['bet_type']
            result = bet['result']
            bet_wins = bet['bet_wins']
            odds = bet['odds']
            stake = bet['stake']
            winnings = bet['winnings']
            momentum_score = bet['momentum_score']
            streak_type = bet['streak_type']
            current_streak = bet['current_streak']
            opponent_momentum_score = bet['opponent_momentum_score']
            
            # Calculate P/L for this bet
            profit_loss = winnings - stake if bet_wins else -stake
            
            # Get recent results for both teams
            bet_team_recent = bet.get('recent_results', [])
            opponent_recent = bet.get('opponent_recent_results', [])
            
            # Format recent results as strings
            bet_team_recent_str = ', '.join(bet_team_recent) if bet_team_recent else 'Not available'
            opponent_recent_str = ', '.join(opponent_recent) if opponent_recent else 'Not available'
            
            # Determine opponent team
            opponent_team = away_team if bet_team == home_team else home_team
            
            # Print to console
            print(f"\n{i:3d}. {match_date} | {home_team} vs {away_team}")
            print(f"     Bet: {bet_team} ({bet_type})")
            print(f"     Odds: {odds:.2f} | Stake: {stake:.1f} | Result: {result} | {'WIN' if bet_wins else 'LOSS'}")
            print(f"     Winnings: {winnings:.1f} | P/L: {profit_loss:+.1f}")
            print(f"     Momentum Score: {momentum_score:.3f} ({streak_type}, {current_streak} streak)")
            print(f"     Opponent Momentum: {opponent_momentum_score:.3f}")
            print(f"     Recent {len(bet_team_recent) if bet_team_recent else lookback_games} games {bet_team}: {bet_team_recent_str}")
            print(f"     Recent {len(opponent_recent) if opponent_recent else lookback_games} games {opponent_team}: {opponent_recent_str}")
            
            # Add to CSV data
            csv_data.append({
                'Bet_Number': i,
                'Match_Date': match_date,
                'Home_Team': home_team,
                'Away_Team': away_team,
                'Bet_Team': bet_team,
                'Bet_Type': bet_type,
                'Match_Result': result,
                'Bet_Wins': 'WIN' if bet_wins else 'LOSS',
                'Odds': odds,
                'Stake': stake,
                'Winnings': winnings,
                'Profit_Loss': profit_loss,
                'Momentum_Score': momentum_score,
                'Streak_Type': streak_type,
                'Current_Streak': current_streak,
                'Opponent_Momentum_Score': opponent_momentum_score,
                'Bet_Team_Recent_Form': bet_team_recent_str,
                'Opponent_Team': opponent_team,
                'Opponent_Recent_Form': opponent_recent_str
            })
        
        # Save to CSV
        self._save_bet_details_to_csv(csv_data)
        
        print("\n" + "="*120)
        print(f"Total Bets: {len(bet_details)}")
        print("="*120)
    
    def _save_bet_details_to_csv(self, csv_data: List[Dict]) -> None:
        """
        Save bet details to CSV file.
        
        Args:
            csv_data (List[Dict]): List of bet details for CSV
        """
        import csv
        from datetime import datetime
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"momentum_bet_details_{timestamp}.csv"
        
        if csv_data:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Bet_Number', 'Match_Date', 'Home_Team', 'Away_Team', 'Bet_Team', 'Bet_Type',
                    'Match_Result', 'Bet_Wins', 'Odds', 'Stake', 'Winnings', 'Profit_Loss',
                    'Momentum_Score', 'Streak_Type', 'Current_Streak', 'Opponent_Momentum_Score',
                    'Bet_Team_Recent_Form', 'Opponent_Team', 'Opponent_Recent_Form'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            
            print(f"\n📊 Bet details saved to: {filename}")
            print(f"💡 You can open this file in Excel for easy analysis!")
        else:
            print("\n❌ No bet data to save to CSV")
