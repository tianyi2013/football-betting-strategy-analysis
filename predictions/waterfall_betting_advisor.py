#!/usr/bin/env python3
"""
Waterfall Betting Advisor: Uses a priority-based approach to betting recommendations
Priority order: Form AGAINST → Momentum AGAINST → Form FOR → Momentum FOR → Top-Bottom (excludes Home-Away)
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from strategies.momentum_strategy import MomentumStrategy
from strategies.form_strategy import FormStrategy
from strategies.top_bottom_strategy import TopBottomStrategy

class WaterfallBettingAdvisor:
    """
    Waterfall betting advisor that uses priority-based strategy selection.
    Priority: Form AGAINST → Momentum AGAINST → Form FOR → Momentum FOR → Top-Bottom
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the waterfall betting advisor.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        self.momentum_strategy = MomentumStrategy(data_directory)
        self.form_strategy = FormStrategy(data_directory)
        self.top_bottom_strategy = TopBottomStrategy(data_directory)
        
        # Strategy priority order (highest to lowest)
        self.strategy_priority = [
            'form_against',        # 1. Most profitable: Form AGAINST bets
            'momentum_against',    # 2. Second: Momentum AGAINST bets
            'form_for',            # 3. Third: Form FOR bets  
            'momentum_for',        # 4. Fourth: Momentum FOR bets
            'top_bottom'           # 5. Fifth: Top-Bottom strategy
        ]
        
        # Strategy performance weights (based on historical ROI)
        self.strategy_weights = {
            'form_against': 0.35,        # Highest weight - most profitable
            'momentum_against': 0.30,    # Second highest - very profitable
            'form_for': 0.15,            # Medium weight - less profitable
            'momentum_for': 0.10,        # Lower weight - less profitable
            'top_bottom': 0.10           # Lowest weight - least profitable
        }
    
    def _normalize_team_name(self, team_name: str) -> str:
        """
        Team names are standardized in upcoming_25.csv.
        No normalization needed.
        
        Args:
            team_name (str): Team name (already standardized)
            
        Returns:
            str: Same team name (no change needed)
        """
        return team_name
    
    def get_betting_recommendations(self, upcoming_games: List[Dict], 
                                  current_season: int = 2024,
                                  match_date: str = None,
                                  form_games: int = 3,
                                  form_threshold: float = 0.6,
                                  poor_form_threshold: float = 0.4,
                                  top_n: int = 3) -> List[Dict]:
        """
        Get betting recommendations using waterfall approach.
        
        Args:
            upcoming_games (List[Dict]): List of upcoming games
            current_season (int): Current season year
            match_date (str): Date to use for calculations (default: today)
            form_games (int): Number of games to consider for form
            form_threshold (float): Minimum form score to bet on team
            poor_form_threshold (float): Maximum form score to bet against team
            top_n (int): Number of top teams for top-bottom strategy
            
        Returns:
            List[Dict]: Betting recommendations for each game
        """
        if match_date is None:
            match_date = datetime.now().strftime('%d/%m/%y')
        
        recommendations = []
        
        for game in upcoming_games:
            home_team = game['home_team']
            away_team = game['away_team']
            game_date = game.get('match_date', match_date)
            
            # Apply waterfall logic
            recommendation = self._apply_waterfall_logic(
                home_team, away_team, current_season, game_date,
                form_games, form_threshold, poor_form_threshold, top_n
            )
            
            recommendations.append({
                'game': f"{home_team} vs {away_team}",
                'home_team': home_team,
                'away_team': away_team,
                'match_date': game_date,
                'recommendation': recommendation
            })
        
        return recommendations
    
    def _apply_waterfall_logic(self, home_team: str, away_team: str, 
                             season: int, match_date: str,
                             form_games: int, form_threshold: float, 
                             poor_form_threshold: float, top_n: int) -> Dict:
        """
        Apply waterfall logic to determine betting recommendation.
        
        Priority order:
        1. Form AGAINST (bet against teams with poor form)
        2. Momentum AGAINST (bet against teams with negative momentum)
        3. Form FOR (bet on teams with good form)
        4. Momentum FOR (bet on teams with positive momentum)
        5. Top-Bottom (bet on top teams vs bottom teams)
        
        Args:
            home_team (str): Home team name
            away_team (str): Away team name
            season (int): Current season
            match_date (str): Match date
            form_games (int): Number of games for form calculation
            form_threshold (float): Good form threshold
            poor_form_threshold (float): Poor form threshold
            top_n (int): Number of top teams
            
        Returns:
            Dict: Betting recommendation
        """
        try:
            # Normalize team names
            home_team_norm = self._normalize_team_name(home_team)
            away_team_norm = self._normalize_team_name(away_team)
            
            # STEP 1: Check for Form AGAINST opportunities (highest priority)
            form_against_rec = self._check_form_against_opportunity(
                home_team_norm, away_team_norm, season, match_date,
                form_games, poor_form_threshold
            )
            
            if form_against_rec['bet_team'] is not None:
                return {
                    'bet_team': form_against_rec['bet_team'],
                    'bet_type': 'FORM_AGAINST',
                    'confidence': form_against_rec['confidence'],
                    'reason': form_against_rec['reason'],
                    'strategy_used': 'form_against',
                    'priority': 1,
                    'detailed_reason': form_against_rec.get('detailed_reason', '')
                }
            
            # STEP 2: Check for Momentum AGAINST opportunities (second priority)
            momentum_against_rec = self._check_momentum_against_opportunity(
                home_team_norm, away_team_norm, season, match_date
            )
            
            if momentum_against_rec['bet_team'] is not None:
                return {
                    'bet_team': momentum_against_rec['bet_team'],
                    'bet_type': 'MOMENTUM_AGAINST',
                    'confidence': momentum_against_rec['confidence'],
                    'reason': momentum_against_rec['reason'],
                    'strategy_used': 'momentum_against',
                    'priority': 2,
                    'detailed_reason': momentum_against_rec.get('detailed_reason', '')
                }
            
            # STEP 3: Check for Form FOR opportunities (third priority)
            form_for_rec = self._check_form_for_opportunity(
                home_team_norm, away_team_norm, season, match_date,
                form_games, form_threshold
            )
            
            if form_for_rec['bet_team'] is not None:
                return {
                    'bet_team': form_for_rec['bet_team'],
                    'bet_type': 'FORM_FOR',
                    'confidence': form_for_rec['confidence'],
                    'reason': form_for_rec['reason'],
                    'strategy_used': 'form_for',
                    'priority': 3,
                    'detailed_reason': form_for_rec.get('detailed_reason', '')
                }
            
            # STEP 4: Check for Momentum FOR opportunities (fourth priority)
            momentum_for_rec = self._check_momentum_for_opportunity(
                home_team_norm, away_team_norm, season, match_date
            )
            
            if momentum_for_rec['bet_team'] is not None:
                return {
                    'bet_team': momentum_for_rec['bet_team'],
                    'bet_type': 'MOMENTUM_FOR',
                    'confidence': momentum_for_rec['confidence'],
                    'reason': momentum_for_rec['reason'],
                    'strategy_used': 'momentum_for',
                    'priority': 4,
                    'detailed_reason': momentum_for_rec.get('detailed_reason', '')
                }
            
            # STEP 5: Check for Top-Bottom opportunities (fifth priority)
            top_bottom_rec = self._check_top_bottom_opportunity(
                home_team_norm, away_team_norm, season, top_n
            )
            
            if top_bottom_rec['bet_team'] is not None:
                return {
                    'bet_team': top_bottom_rec['bet_team'],
                    'bet_type': 'TOP_BOTTOM',
                    'confidence': top_bottom_rec['confidence'],
                    'reason': top_bottom_rec['reason'],
                    'strategy_used': 'top_bottom',
                    'priority': 5,
                    'detailed_reason': top_bottom_rec.get('detailed_reason', '')
                }
            
            # No betting opportunity found
            return {
                'bet_team': None,
                'bet_type': None,
                'confidence': 0,
                'reason': 'No betting opportunities found in any strategy',
                'strategy_used': None,
                'priority': None,
                'detailed_reason': 'Checked: Form AGAINST, Momentum AGAINST, Form FOR, Momentum FOR, Top-Bottom - no opportunities'
            }
            
        except Exception as e:
            return {
                'bet_team': None,
                'bet_type': None,
                'confidence': 0,
                'reason': f'Error in waterfall logic: {str(e)}',
                'strategy_used': None,
                'priority': None,
                'detailed_reason': f'Exception: {str(e)}'
            }
    
    def _check_form_against_opportunity(self, home_team: str, away_team: str,
                                      season: int, match_date: str,
                                      form_games: int, poor_form_threshold: float) -> Dict:
        """
        Check for Form AGAINST betting opportunities.
        
        Returns:
            Dict: Recommendation if opportunity exists
        """
        try:
            # Calculate form for both teams
            home_form = self.form_strategy.calculate_team_form(
                home_team, season, match_date, form_games
            )
            away_form = self.form_strategy.calculate_team_form(
                away_team, season, match_date, form_games
            )
            
            if 'error' in home_form or 'error' in away_form:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            if home_form['games_played'] < form_games or away_form['games_played'] < form_games:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient games'}
            
            home_form_score = home_form['form_score']
            away_form_score = away_form['form_score']
            
            # Check if home team has poor form (bet against them)
            if home_form_score <= poor_form_threshold:
                return {
                    'bet_team': home_team,  # Bet AGAINST home team
                    'confidence': min((poor_form_threshold - home_form_score) * 2, 1.0),
                    'reason': f'Home team poor form ({home_form_score:.2f}) vs threshold ({poor_form_threshold})',
                    'detailed_reason': f'Home team form: {home_form_score:.2f} ≤ {poor_form_threshold} (poor form threshold)'
                }
            
            # Check if away team has poor form (bet against them)
            if away_form_score <= poor_form_threshold:
                return {
                    'bet_team': away_team,  # Bet AGAINST away team
                    'confidence': min((poor_form_threshold - away_form_score) * 2, 1.0),
                    'reason': f'Away team poor form ({away_form_score:.2f}) vs threshold ({poor_form_threshold})',
                    'detailed_reason': f'Away team form: {away_form_score:.2f} ≤ {poor_form_threshold} (poor form threshold)'
                }
            
            return {'bet_team': None, 'confidence': 0, 'reason': 'No poor form teams found'}
            
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _check_momentum_against_opportunity(self, home_team: str, away_team: str,
                                          season: int, match_date: str) -> Dict:
        """
        Check for Momentum AGAINST betting opportunities.
        
        Returns:
            Dict: Recommendation if opportunity exists
        """
        try:
            # Calculate momentum for both teams
            home_momentum = self.momentum_strategy.calculate_team_momentum(
                home_team, season, match_date, lookback_games=10
            )
            away_momentum = self.momentum_strategy.calculate_team_momentum(
                away_team, season, match_date, lookback_games=10
            )
            
            if 'error' in home_momentum or 'error' in away_momentum:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            if home_momentum['games_played'] < 10 or away_momentum['games_played'] < 10:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient games'}
            
            home_momentum_score = home_momentum['momentum_score']
            away_momentum_score = away_momentum['momentum_score']
            
            # Momentum thresholds
            losing_momentum_threshold = -0.2  # Negative momentum threshold
            
            # Check if home team has negative momentum (bet against them)
            if home_momentum_score <= losing_momentum_threshold:
                return {
                    'bet_team': home_team,  # Bet AGAINST home team
                    'confidence': min(abs(losing_momentum_threshold - home_momentum_score) * 2, 1.0),
                    'reason': f'Home team negative momentum ({home_momentum_score:.2f}) vs threshold ({losing_momentum_threshold})',
                    'detailed_reason': f'Home team momentum: {home_momentum_score:.2f} ≤ {losing_momentum_threshold} (negative momentum threshold)'
                }
            
            # Check if away team has negative momentum (bet against them)
            if away_momentum_score <= losing_momentum_threshold:
                return {
                    'bet_team': away_team,  # Bet AGAINST away team
                    'confidence': min(abs(losing_momentum_threshold - away_momentum_score) * 2, 1.0),
                    'reason': f'Away team negative momentum ({away_momentum_score:.2f}) vs threshold ({losing_momentum_threshold})',
                    'detailed_reason': f'Away team momentum: {away_momentum_score:.2f} ≤ {losing_momentum_threshold} (negative momentum threshold)'
                }
            
            return {'bet_team': None, 'confidence': 0, 'reason': 'No negative momentum teams found'}
            
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _check_momentum_for_opportunity(self, home_team: str, away_team: str,
                                     season: int, match_date: str) -> Dict:
        """
        Check for Momentum FOR betting opportunities.
        
        Returns:
            Dict: Recommendation if opportunity exists
        """
        try:
            # Calculate momentum for both teams
            home_momentum = self.momentum_strategy.calculate_team_momentum(
                home_team, season, match_date, lookback_games=10
            )
            away_momentum = self.momentum_strategy.calculate_team_momentum(
                away_team, season, match_date, lookback_games=10
            )
            
            if 'error' in home_momentum or 'error' in away_momentum:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            if home_momentum['games_played'] < 10 or away_momentum['games_played'] < 10:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient games'}
            
            home_momentum_score = home_momentum['momentum_score']
            away_momentum_score = away_momentum['momentum_score']
            
            # Momentum thresholds
            winning_momentum_threshold = 0.2  # Positive momentum threshold
            
            # Check if home team has positive momentum
            if home_momentum_score >= winning_momentum_threshold:
                return {
                    'bet_team': home_team,  # Bet FOR home team
                    'confidence': min((home_momentum_score - winning_momentum_threshold) * 2, 1.0),
                    'reason': f'Home team positive momentum ({home_momentum_score:.2f}) vs threshold ({winning_momentum_threshold})',
                    'detailed_reason': f'Home team momentum: {home_momentum_score:.2f} ≥ {winning_momentum_threshold} (positive momentum threshold)'
                }
            
            # Check if away team has positive momentum
            if away_momentum_score >= winning_momentum_threshold:
                return {
                    'bet_team': away_team,  # Bet FOR away team
                    'confidence': min((away_momentum_score - winning_momentum_threshold) * 2, 1.0),
                    'reason': f'Away team positive momentum ({away_momentum_score:.2f}) vs threshold ({winning_momentum_threshold})',
                    'detailed_reason': f'Away team momentum: {away_momentum_score:.2f} ≥ {winning_momentum_threshold} (positive momentum threshold)'
                }
            
            return {'bet_team': None, 'confidence': 0, 'reason': 'No positive momentum teams found'}
            
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _check_form_for_opportunity(self, home_team: str, away_team: str,
                                  season: int, match_date: str,
                                  form_games: int, form_threshold: float) -> Dict:
        """
        Check for Form FOR betting opportunities.
        
        Returns:
            Dict: Recommendation if opportunity exists
        """
        try:
            # Calculate form for both teams
            home_form = self.form_strategy.calculate_team_form(
                home_team, season, match_date, form_games
            )
            away_form = self.form_strategy.calculate_team_form(
                away_team, season, match_date, form_games
            )
            
            if 'error' in home_form or 'error' in away_form:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            if home_form['games_played'] < form_games or away_form['games_played'] < form_games:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Insufficient games'}
            
            home_form_score = home_form['form_score']
            away_form_score = away_form['form_score']
            
            # Check if home team has good form
            if home_form_score >= form_threshold:
                return {
                    'bet_team': home_team,  # Bet FOR home team
                    'confidence': min((home_form_score - form_threshold) * 2, 1.0),
                    'reason': f'Home team good form ({home_form_score:.2f}) vs threshold ({form_threshold})',
                    'detailed_reason': f'Home team form: {home_form_score:.2f} ≥ {form_threshold} (good form threshold)'
                }
            
            # Check if away team has good form
            if away_form_score >= form_threshold:
                return {
                    'bet_team': away_team,  # Bet FOR away team
                    'confidence': min((away_form_score - form_threshold) * 2, 1.0),
                    'reason': f'Away team good form ({away_form_score:.2f}) vs threshold ({form_threshold})',
                    'detailed_reason': f'Away team form: {away_form_score:.2f} ≥ {form_threshold} (good form threshold)'
                }
            
            return {'bet_team': None, 'confidence': 0, 'reason': 'No good form teams found'}
            
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}
    
    def _check_top_bottom_opportunity(self, home_team: str, away_team: str,
                                    season: int, top_n: int) -> Dict:
        """
        Check for Top-Bottom betting opportunities.
        
        Returns:
            Dict: Recommendation if opportunity exists
        """
        try:
            # Get league standings from previous season
            previous_season = season - 1
            standings = self.top_bottom_strategy.analytics.get_league_standings(previous_season)
            
            if standings.empty:
                return {'bet_team': None, 'confidence': 0, 'reason': 'No standings data'}
            
            # Find team positions
            home_position = None
            away_position = None
            
            for _, row in standings.iterrows():
                if row['team'] == home_team:
                    home_position = row['rank']
                elif row['team'] == away_team:
                    away_position = row['rank']
            
            if home_position is None or away_position is None:
                return {'bet_team': None, 'confidence': 0, 'reason': 'Team not found in standings'}
            
            # Check for top vs bottom matchups
            if home_position <= top_n and away_position >= (20 - top_n + 1):  # Top vs Bottom
                return {
                    'bet_team': home_team,  # Bet FOR top team
                    'confidence': 0.8,
                    'reason': f'Top {home_position} vs Bottom {away_position}',
                    'detailed_reason': f'Home team: {home_position} (top {top_n}) vs Away team: {away_position} (bottom {top_n})'
                }
            elif away_position <= top_n and home_position >= (20 - top_n + 1):  # Top vs Bottom
                return {
                    'bet_team': away_team,  # Bet FOR top team
                    'confidence': 0.8,
                    'reason': f'Top {away_position} vs Bottom {home_position}',
                    'detailed_reason': f'Away team: {away_position} (top {top_n}) vs Home team: {home_position} (bottom {top_n})'
                }
            
            return {'bet_team': None, 'confidence': 0, 'reason': 'No top-bottom advantage'}
            
        except Exception as e:
            return {'bet_team': None, 'confidence': 0, 'reason': f'Error: {str(e)}'}


def get_waterfall_betting_advice(upcoming_games: List[Dict], current_season: int = 2024) -> List[Dict]:
    """
    Convenience function to get waterfall betting advice for upcoming games.
    
    Args:
        upcoming_games (List[Dict]): List of upcoming games
        current_season (int): Current season year
        
    Returns:
        List[Dict]: Betting recommendations
    """
    advisor = WaterfallBettingAdvisor()
    return advisor.get_betting_recommendations(upcoming_games, current_season)
