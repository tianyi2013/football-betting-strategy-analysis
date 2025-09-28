#!/usr/bin/env python3
"""
Betting Advisor: Provides betting recommendations for upcoming games
using your proven strategies (Momentum, Form, Top-Bottom, Home/Away)
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from strategies.momentum_strategy import MomentumStrategy
from strategies.form_strategy import FormStrategy
from strategies.top_bottom_strategy import TopBottomStrategy
from strategies.home_away_strategy import HomeAwayStrategy

class BettingAdvisor:
    """
    Provides betting recommendations for upcoming games using proven strategies.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the betting advisor with all strategies.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        self.momentum_strategy = MomentumStrategy(data_directory)
        self.form_strategy = FormStrategy(data_directory)
        self.top_bottom_strategy = TopBottomStrategy(data_directory)
        self.home_away_strategy = HomeAwayStrategy(data_directory)
        
        # Team names are now standardized in upcoming_25.csv
        # No mapping needed anymore
        
        # Strategy weights based on performance (ROI)
        self.strategy_weights = {
            'momentum': 0.40,    # Best performer: +83.6% ROI
            'form': 0.30,        # Second best: +75.8% ROI
            'top_bottom': 0.20,  # Third best: +70.6% ROI
            'home_away': 0.10    # Fourth: -3.3% ROI (but still useful)
        }
    
    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team names to match historical data format.
        
        Args:
            team_name (str): Team name from upcoming games
            
        Returns:
            str: Normalized team name for historical data lookup
        """
        # La Liga team name mappings
        la_liga_mappings = {
            'Girona FC': 'Girona',
            'Villarreal CF': 'Villarreal', 
            'RCD Mallorca': 'Mallorca',
            'Deportivo Alavés': 'Alaves',
            'Valencia CF': 'Valencia',
            'Athletic Club': 'Ath Bilbao',
            'RCD Espanyol de Barcelona': 'Espanol',
            'Elche CF': 'Elche',
            'Real Madrid': 'Real Madrid',
            'FC Barcelona': 'Barcelona',
            'Atlético de Madrid': 'Ath Madrid',
            'Sevilla FC': 'Sevilla',
            'Real Sociedad': 'Sociedad',
            'CA Osasuna': 'Osasuna',
            'Real Betis': 'Betis',
            'Rayo Vallecano': 'Vallecano',
            'Levante UD': 'Levante',
            'Real Oviedo': 'Oviedo',
            'Celta': 'Celta',
            'Hellas Verona': 'Verona'
        }
        
        # Ligue 1 team name mappings
        ligue1_mappings = {
            'Angers SCO': 'Angers',
            'AJ Auxerre': 'Auxerre',
            'Stade Brestois 29': 'Brest',
            'RC Lens': 'Lens',
            'FC Metz': 'Metz',
            'AS Monaco': 'Monaco',
            'FC Nantes': 'Nantes',
            'OGC Nice': 'Nice',
            'Stade Rennais FC': 'Rennes',
            'Havre Athletic Club': 'Le Havre',
            'Paris Saint-Germain': 'Paris SG',
            'Olympique Lyonnais': 'Lyon',
            'LOSC Lille': 'Lille',
            'FC Lorient': 'Lorient',
            'RC Strasbourg Alsace': 'Strasbourg',
            'Olympique de Marseille': 'Marseille',
            'Toulouse FC': 'Toulouse',
            'FC Nantes': 'Nantes'
        }
        
        # Check if it's a known mapping
        if team_name in la_liga_mappings:
            return la_liga_mappings[team_name]
        elif team_name in ligue1_mappings:
            return ligue1_mappings[team_name]
        
        # For other leagues, return as-is
        return team_name
    
    def get_betting_recommendations(self, upcoming_games: List[Dict], 
                                  current_season: int = 2024,
                                  match_date: str = None) -> List[Dict]:
        """
        Get betting recommendations for upcoming games.
        
        Args:
            upcoming_games (List[Dict]): List of upcoming games with format:
                [{'home_team': 'Arsenal', 'away_team': 'Chelsea', 'match_date': '2024-01-15'}, ...]
            current_season (int): Current season year
            match_date (str): Date to use for calculations (default: today)
            
        Returns:
            List[Dict]: Betting recommendations for each game
        """
        if match_date is None:
            match_date = datetime.now().strftime('%Y-%m-%d')
        
        recommendations = []
        
        for game in upcoming_games:
            home_team = game['home_team']
            away_team = game['away_team']
            game_date = game.get('match_date', match_date)
            
            # Get recommendations from each strategy
            momentum_rec = self._get_momentum_recommendation(home_team, away_team, current_season, match_date)
            form_rec = self._get_form_recommendation(home_team, away_team, current_season, match_date)
            top_bottom_rec = self._get_top_bottom_recommendation(home_team, away_team, current_season)
            home_away_rec = self._get_home_away_recommendation(home_team, away_team, current_season)
            
            # Calculate weighted recommendation
            weighted_rec = self._calculate_weighted_recommendation(
                momentum_rec, form_rec, top_bottom_rec, home_away_rec
            )
            
            recommendations.append({
                'game': f"{home_team} vs {away_team}",
                'home_team': home_team,
                'away_team': away_team,
                'match_date': game_date,
                'recommendation': weighted_rec,
                'individual_strategies': {
                    'momentum': momentum_rec,
                    'form': form_rec,
                    'top_bottom': top_bottom_rec,
                    'home_away': home_away_rec
                }
            })
        
        return recommendations
    
    def _get_momentum_recommendation(self, home_team: str, away_team: str, 
                                   season: int, match_date: str) -> Dict:
        """Get momentum-based recommendation."""
        try:
            # Normalize team names
            home_team_norm = self._normalize_team_name(home_team)
            away_team_norm = self._normalize_team_name(away_team)
            
            # Calculate momentum for both teams
            home_momentum = self.momentum_strategy.calculate_team_momentum(
                home_team_norm, season, match_date, lookback_games=3
            )
            away_momentum = self.momentum_strategy.calculate_team_momentum(
                away_team_norm, season, match_date, lookback_games=3
            )
            
            if 'error' in home_momentum or 'error' in away_momentum:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            if home_momentum['games_played'] < 3 or away_momentum['games_played'] < 3:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient games'}
            
            # Determine recommendation based on momentum
            home_momentum_score = home_momentum['momentum_score']
            away_momentum_score = away_momentum['momentum_score']
            
            # Strong momentum threshold
            strong_momentum_threshold = 0.2
            weak_momentum_threshold = -0.2
            
            # Get recent results for both teams
            home_recent_results = home_momentum.get('recent_results', [])
            away_recent_results = away_momentum.get('recent_results', [])
            
            # Create detailed reason with recent games and scores
            detailed_reason = f"Home team: {home_recent_results} (Score: {home_momentum_score:.2f}) | Away team: {away_recent_results} (Score: {away_momentum_score:.2f}) | Thresholds: Strong ≥{strong_momentum_threshold}, Weak ≤{weak_momentum_threshold}"
            
            if home_momentum_score >= strong_momentum_threshold and away_momentum_score <= weak_momentum_threshold:
                return {
                    'bet_team': home_team,
                    'confidence': min(abs(home_momentum_score - away_momentum_score) * 2, 1.0),
                    'reason': f'Home team strong momentum ({home_momentum_score:.2f}) vs away team weak momentum ({away_momentum_score:.2f})',
                    'detailed_reason': detailed_reason
                }
            elif away_momentum_score >= strong_momentum_threshold and home_momentum_score <= weak_momentum_threshold:
                return {
                    'bet_team': away_team,
                    'confidence': min(abs(away_momentum_score - home_momentum_score) * 2, 1.0),
                    'reason': f'Away team strong momentum ({away_momentum_score:.2f}) vs home team weak momentum ({home_momentum_score:.2f})',
                    'detailed_reason': detailed_reason
                }
            else:
                return {
                    'bet_team': None, 
                    'confidence': 0, 
                    'reason': 'No clear momentum advantage',
                    'detailed_reason': detailed_reason
                }
                
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _get_form_recommendation(self, home_team: str, away_team: str, 
                               season: int, match_date: str) -> Dict:
        """Get form-based recommendation."""
        try:
            # Normalize team names
            home_team_norm = self._normalize_team_name(home_team)
            away_team_norm = self._normalize_team_name(away_team)
            
            # Calculate form for both teams
            home_form = self.form_strategy.calculate_team_form(
                home_team_norm, season, match_date, form_games=3
            )
            away_form = self.form_strategy.calculate_team_form(
                away_team_norm, season, match_date, form_games=3
            )
            
            if 'error' in home_form or 'error' in away_form:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            if home_form['games_played'] < 3 or away_form['games_played'] < 3:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient games'}
            
            # Determine recommendation based on form
            home_form_score = home_form['form_score']
            away_form_score = away_form['form_score']
            
            # Form threshold
            good_form_threshold = 0.6
            poor_form_threshold = 0.4
            
            # Get recent results and points for both teams
            home_recent_results = home_form.get('recent_results', [])
            away_recent_results = away_form.get('recent_results', [])
            home_points = home_form.get('points', 0)
            away_points = away_form.get('points', 0)
            
            # Create detailed reason with recent games, points, and scores
            detailed_reason = f"Home team: {home_recent_results} ({home_points} pts, Score: {home_form_score:.2f}) | Away team: {away_recent_results} ({away_points} pts, Score: {away_form_score:.2f}) | Thresholds: Good ≥{good_form_threshold}, Poor ≤{poor_form_threshold}"
            
            if home_form_score >= good_form_threshold and away_form_score <= poor_form_threshold:
                return {
                    'bet_team': home_team,
                    'confidence': min(abs(home_form_score - away_form_score) * 2, 1.0),
                    'reason': f'Home team good form ({home_form_score:.2f}) vs away team poor form ({away_form_score:.2f})',
                    'detailed_reason': detailed_reason
                }
            elif away_form_score >= good_form_threshold and home_form_score <= poor_form_threshold:
                return {
                    'bet_team': away_team,
                    'confidence': min(abs(away_form_score - home_form_score) * 2, 1.0),
                    'reason': f'Away team good form ({away_form_score:.2f}) vs home team poor form ({home_form_score:.2f})',
                    'detailed_reason': detailed_reason
                }
            else:
                return {
                    'bet_team': None, 
                    'confidence': 0, 
                    'reason': 'No clear form advantage',
                    'detailed_reason': detailed_reason
                }
                
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _get_top_bottom_recommendation(self, home_team: str, away_team: str, 
                                     season: int) -> Dict:
        """Get top-bottom recommendation."""
        try:
            # Normalize team names
            home_team_norm = self._normalize_team_name(home_team)
            away_team_norm = self._normalize_team_name(away_team)
            
            # Get league standings
            standings = self.top_bottom_strategy.analytics.get_league_standings(season)
            
            if standings.empty:
                return {'bet_team': None, 'confidence': 0, 'reason': 'No standings data'}
            
            # Find team positions
            home_position = None
            away_position = None
            
            for _, row in standings.iterrows():
                if row['team'] == home_team_norm:
                    home_position = row['rank']
                elif row['team'] == away_team_norm:
                    away_position = row['rank']
            
            if home_position is None or away_position is None:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Team not found in standings'}
            
            # Get top 3 and bottom 3 teams for detailed explanation
            top_3_teams = []
            bottom_3_teams = []
            
            for _, row in standings.iterrows():
                if row['rank'] <= 3:
                    top_3_teams.append(row['team'])
                elif row['rank'] >= 18:
                    bottom_3_teams.append(row['team'])
            
            # Create detailed reason with top/bottom teams
            detailed_reason = f"Top 3: {', '.join(top_3_teams)} | Bottom 3: {', '.join(bottom_3_teams)} | Teams: {home_team_norm} (pos {home_position}), {away_team_norm} (pos {away_position})"
            
            # Top 3 vs Bottom 3 logic
            if home_position <= 3 and away_position >= 18:  # Home team top 3, away team bottom 3
                return {
                    'bet_team': home_team,
                    'confidence': 0.8,
                    'reason': f'Home team top {home_position} vs away team bottom {away_position}',
                    'detailed_reason': detailed_reason
                }
            elif away_position <= 3 and home_position >= 18:  # Away team top 3, home team bottom 3
                return {
                    'bet_team': away_team,
                    'confidence': 0.8,
                    'reason': f'Away team top {away_position} vs home team bottom {home_position}',
                    'detailed_reason': detailed_reason
                }
            else:
                return {
                    'bet_team': None, 
                    'confidence': 0, 
                    'reason': 'No top-bottom advantage',
                    'detailed_reason': detailed_reason
                }
                
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _get_home_away_recommendation(self, home_team: str, away_team: str, 
                                    season: int) -> Dict:
        """Get home-away recommendation."""
        try:
            # Normalize team names
            home_team_norm = self._normalize_team_name(home_team)
            away_team_norm = self._normalize_team_name(away_team)
            
            # Calculate home and away records
            home_record = self.home_away_strategy.analytics.get_team_home_record(home_team_norm, season)
            away_record = self.home_away_strategy.analytics.get_team_away_record(away_team_norm, season)
            
            if 'error' in home_record or 'error' in away_record:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            # Calculate win rates
            home_win_rate = home_record['wins'] / home_record['games'] if home_record['games'] > 0 else 0
            away_win_rate = away_record['wins'] / away_record['games'] if away_record['games'] > 0 else 0
            
            # Home advantage threshold
            home_advantage_threshold = 0.1  # 10% difference
            
            if home_win_rate - away_win_rate >= home_advantage_threshold:
                return {
                    'bet_team': home_team,
                    'confidence': min((home_win_rate - away_win_rate) * 3, 1.0),
                    'reason': f'Home team strong home record ({home_win_rate:.1%}) vs away team weak away record ({away_win_rate:.1%})'
                }
            elif away_win_rate - home_win_rate >= home_advantage_threshold:
                return {
                    'bet_team': away_team,
                    'confidence': min((away_win_rate - home_win_rate) * 3, 1.0),
                    'reason': f'Away team strong away record ({away_win_rate:.1%}) vs home team weak home record ({home_win_rate:.1%})'
                }
            else:
                return {'bet_team': None, 'confidence': 0, 'reason': 'No clear home/away advantage'}
                
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _calculate_weighted_recommendation(self, momentum_rec: Dict, form_rec: Dict, 
                                         top_bottom_rec: Dict, home_away_rec: Dict) -> Dict:
        """Calculate weighted recommendation based on strategy performance."""
        
        # Collect all recommendations
        recommendations = []
        
        if momentum_rec['bet_team']:
            recommendations.append({
                'team': momentum_rec['bet_team'],
                'weight': self.strategy_weights['momentum'],
                'confidence': momentum_rec['confidence'],
                'strategy': 'momentum',
                'reason': momentum_rec['reason']
            })
        
        if form_rec['bet_team']:
            recommendations.append({
                'team': form_rec['bet_team'],
                'weight': self.strategy_weights['form'],
                'confidence': form_rec['confidence'],
                'strategy': 'form',
                'reason': form_rec['reason']
            })
        
        if top_bottom_rec['bet_team']:
            recommendations.append({
                'team': top_bottom_rec['bet_team'],
                'weight': self.strategy_weights['top_bottom'],
                'confidence': top_bottom_rec['confidence'],
                'strategy': 'top_bottom',
                'reason': top_bottom_rec['reason']
            })
        
        if home_away_rec['bet_team']:
            recommendations.append({
                'team': home_away_rec['bet_team'],
                'weight': self.strategy_weights['home_away'],
                'confidence': home_away_rec['confidence'],
                'strategy': 'home_away',
                'reason': home_away_rec['reason']
            })
        
        if not recommendations:
            return {
                'bet_team': None,
                'confidence': 0,
                'reason': 'No strategies recommend betting',
                'supporting_strategies': []
            }
        
        # Calculate weighted scores for each team
        team_scores = {}
        team_reasons = {}
        
        for rec in recommendations:
            team = rec['team']
            if team not in team_scores:
                team_scores[team] = 0
                team_reasons[team] = []
            
            # Weighted score = strategy_weight * confidence
            weighted_score = rec['weight'] * rec['confidence']
            team_scores[team] += weighted_score
            team_reasons[team].append(f"{rec['strategy']}: {rec['reason']}")
        
        # Find the team with highest weighted score
        best_team = max(team_scores.items(), key=lambda x: x[1])
        
        return {
            'bet_team': best_team[0],
            'confidence': min(best_team[1], 1.0),
            'reason': f"Weighted recommendation based on {len(team_scores)} strategies",
            'supporting_strategies': team_reasons[best_team[0]],
            'all_scores': team_scores
        }


def get_betting_advice(upcoming_games: List[Dict], current_season: int = 2024) -> List[Dict]:
    """
    Convenience function to get betting advice for upcoming games.
    
    Args:
        upcoming_games (List[Dict]): List of upcoming games
        current_season (int): Current season year
        
    Returns:
        List[Dict]: Betting recommendations
    """
    advisor = BettingAdvisor()
    return advisor.get_betting_recommendations(upcoming_games, current_season)
