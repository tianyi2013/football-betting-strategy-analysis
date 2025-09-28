"""
Premier League Analytics - Core league table analysis functionality
"""

import pandas as pd
import os
from typing import Dict, List, Tuple, Optional

class PremierLeagueAnalytics:
    """
    Core analytics for Premier League data analysis.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the analytics with data directory.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        self.data_directory = data_directory
        self.available_seasons = self._get_available_seasons()
        
    def _get_available_seasons(self) -> List[int]:
        """Get list of available seasons from CSV files."""
        seasons = []
        if os.path.exists(self.data_directory):
            for filename in os.listdir(self.data_directory):
                if filename.endswith('.csv'):
                    try:
                        season = int(filename.replace('.csv', ''))
                        seasons.append(season)
                    except ValueError:
                        continue
        return sorted(seasons)
    
    def load_season_data(self, season_year: int) -> pd.DataFrame:
        """
        Load season data from CSV file.
        
        Args:
            season_year (int): Starting year of the season
            
        Returns:
            pd.DataFrame: Season data
        """
        file_path = os.path.join(self.data_directory, f"{season_year}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Season {season_year} data not found")
        
        # Handle BOM and encoding issues
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin-1')
        
        # Clean column names by stripping whitespace and BOM
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        
        return df
    
    def get_league_table(self, season_year: int) -> pd.DataFrame:
        """
        Get league table for a specific season.
        
        Args:
            season_year (int): Starting year of the season
            
        Returns:
            pd.DataFrame: League table with team rankings
        """
        file_path = os.path.join(self.data_directory, f"{season_year}.csv")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Season {season_year} data not found")
        
        df = pd.read_csv(file_path, on_bad_lines='skip', encoding='latin-1')
        
        # Validate required columns
        required_columns = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Calculate team statistics
        team_stats = {}
        
        for _, match in df.iterrows():
            # Skip rows with missing essential data
            if pd.isna(match['HomeTeam']) or pd.isna(match['AwayTeam']) or \
               pd.isna(match['FTHG']) or pd.isna(match['FTAG']) or pd.isna(match['FTR']):
                continue
                
            home_team = match['HomeTeam']
            away_team = match['AwayTeam']
            home_goals = int(match['FTHG'])
            away_goals = int(match['FTAG'])
            result = match['FTR']
            
            # Initialize team stats if not exists
            for team in [home_team, away_team]:
                if team not in team_stats:
                    team_stats[team] = {
                        'points': 0, 'wins': 0, 'draws': 0, 'losses': 0,
                        'goals_for': 0, 'goals_against': 0, 'matches_played': 0
                    }
            
            # Update home team stats
            team_stats[home_team]['goals_for'] += home_goals
            team_stats[home_team]['goals_against'] += away_goals
            team_stats[home_team]['matches_played'] += 1
            
            # Update away team stats
            team_stats[away_team]['goals_for'] += away_goals
            team_stats[away_team]['goals_against'] += home_goals
            team_stats[away_team]['matches_played'] += 1
            
            # Assign points based on result
            if result == 'H':  # Home win
                team_stats[home_team]['points'] += 3
                team_stats[home_team]['wins'] += 1
                team_stats[away_team]['losses'] += 1
            elif result == 'A':  # Away win
                team_stats[away_team]['points'] += 3
                team_stats[away_team]['wins'] += 1
                team_stats[home_team]['losses'] += 1
            else:  # Draw
                team_stats[home_team]['points'] += 1
                team_stats[away_team]['points'] += 1
                team_stats[home_team]['draws'] += 1
                team_stats[away_team]['draws'] += 1
        
        # Calculate goal difference and create DataFrame
        for team in team_stats:
            team_stats[team]['goal_difference'] = (
                team_stats[team]['goals_for'] - team_stats[team]['goals_against']
            )
        
        # Convert to DataFrame and sort by points, then goal difference
        league_data = []
        for team, stats in team_stats.items():
            league_data.append({
                'team': team,
                'points': stats['points'],
                'matches_played': stats['matches_played'],
                'wins': stats['wins'],
                'draws': stats['draws'],
                'losses': stats['losses'],
                'goals_for': stats['goals_for'],
                'goals_against': stats['goals_against'],
                'goal_difference': stats['goal_difference']
            })
        
        df_league = pd.DataFrame(league_data)
        df_league = df_league.sort_values(['points', 'goal_difference'], ascending=[False, False])
        df_league = df_league.reset_index(drop=True)
        df_league['rank'] = df_league.index + 1
        
        return df_league
    
    def get_top_teams(self, season_year: int, n: int) -> List[str]:
        """
        Get top N teams from a specific season.
        
        Args:
            season_year (int): Starting year of the season
            n (int): Number of top teams to select
            
        Returns:
            List[str]: List of top N team names
        """
        league_table = self.get_league_table(season_year)
        return league_table.head(n)['team'].tolist()
    
    def get_bottom_teams(self, season_year: int, n: int) -> List[str]:
        """
        Get bottom N teams from a specific season (excluding relegated teams).
        
        Args:
            season_year (int): Starting year of the season
            n (int): Number of bottom teams to select (excluding relegated teams)
            
        Returns:
            List[str]: List of bottom N team names (excluding relegated teams)
        """
        league_table = self.get_league_table(season_year)
        # Get bottom teams but exclude the last 3 (relegated teams)
        bottom_teams = league_table.tail(n + 3).head(n)['team'].tolist()
        return bottom_teams
    
    def print_league_table(self, season_year: int) -> None:
        """
        Print a formatted league table for a specific season.
        
        Args:
            season_year (int): Starting year of the season
        """
        league_table = self.get_league_table(season_year)
        
        print(f"\n{'='*80}")
        print(f"PREMIER LEAGUE {season_year}-{str(season_year + 1)[-2:]} - FINAL TABLE")
        print(f"{'='*80}")
        print(f"Total Teams: {len(league_table)} | Total Matches: {len(league_table) * 2}")
        print(f"{'='*80}")
        
        # Header
        print(f"{'Pos':<4} {'Team':<20} {'P':<3} {'W':<3} {'D':<3} {'L':<3} {'GF':<3} {'GA':<3} {'GD':<4} {'Pts':<4}")
        print(f"{'-'*80}")
        
        # Team rows
        for _, team in league_table.iterrows():
            print(f"{team['rank']:<4} {team['team']:<20} {team['matches_played']:<3} "
                  f"{team['wins']:<3} {team['draws']:<3} {team['losses']:<3} "
                  f"{team['goals_for']:<3} {team['goals_against']:<3} {team['goal_difference']:<4} "
                  f"{team['points']:<4}")
        
        print(f"{'='*80}")
    
    def get_league_standings(self, season_year: int) -> pd.DataFrame:
        """
        Get league standings for a specific season.
        This is an alias for get_league_table to maintain compatibility.
        
        Args:
            season_year (int): Starting year of the season
            
        Returns:
            pd.DataFrame: League standings with team rankings
        """
        return self.get_league_table(season_year)
    
    def get_team_home_record(self, team_name: str, season_year: int) -> Dict:
        """
        Get home record for a specific team in a season.
        
        Args:
            team_name (str): Name of the team
            season_year (int): Starting year of the season
            
        Returns:
            Dict: Home record statistics
        """
        try:
            df = self.load_season_data(season_year)
            if df.empty:
                return {'error': f'No data available for season {season_year}'}
            
            # Filter for home games of the team
            home_games = df[df['HomeTeam'] == team_name]
            
            if home_games.empty:
                return {'error': f'No home games found for {team_name} in season {season_year}'}
            
            # Calculate home record
            wins = len(home_games[home_games['FTR'] == 'H'])
            draws = len(home_games[home_games['FTR'] == 'D'])
            losses = len(home_games[home_games['FTR'] == 'A'])
            games = len(home_games)
            
            return {
                'team': team_name,
                'season': season_year,
                'games': games,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': wins / games if games > 0 else 0,
                'points': wins * 3 + draws
            }
        except Exception as e:
            return {'error': f'Error getting home record for {team_name}: {str(e)}'}
    
    def get_team_away_record(self, team_name: str, season_year: int) -> Dict:
        """
        Get away record for a specific team in a season.
        
        Args:
            team_name (str): Name of the team
            season_year (int): Starting year of the season
            
        Returns:
            Dict: Away record statistics
        """
        try:
            df = self.load_season_data(season_year)
            if df.empty:
                return {'error': f'No data available for season {season_year}'}
            
            # Filter for away games of the team
            away_games = df[df['AwayTeam'] == team_name]
            
            if away_games.empty:
                return {'error': f'No away games found for {team_name} in season {season_year}'}
            
            # Calculate away record
            wins = len(away_games[away_games['FTR'] == 'A'])
            draws = len(away_games[away_games['FTR'] == 'D'])
            losses = len(away_games[away_games['FTR'] == 'H'])
            games = len(away_games)
            
            return {
                'team': team_name,
                'season': season_year,
                'games': games,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'win_rate': wins / games if games > 0 else 0,
                'points': wins * 3 + draws
            }
        except Exception as e:
            return {'error': f'Error getting away record for {team_name}: {str(e)}'}