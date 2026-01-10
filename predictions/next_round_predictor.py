#!/usr/bin/env python3
"""
Next Round Predictor: Reads upcoming games from CSV and provides betting predictions
for the next round of games that haven't been played yet.
"""
from datetime import datetime
from typing import Dict

import pandas as pd

from .betting_advisor import BettingAdvisor


class NextRoundPredictor:
    """
    Predicts betting recommendations for the next round of upcoming games.
    """

    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the next round predictor.
        
        Args:
            data_directory (str): Path to directory containing data files
        """
        self.data_directory = data_directory
        self.betting_advisor = BettingAdvisor(data_directory)
        self.upcoming_file = f"{data_directory}/upcoming_25.csv"

    def get_next_round_predictions(self, current_date: str = None) -> Dict:
        """
        Get betting predictions for the next round of upcoming games.
        
        Args:
            current_date (str): Current date in format 'YYYY-MM-DD' (default: today)
            
        Returns:
            Dict: Predictions for the next round with metadata
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')

        try:
            # Load upcoming games - try UTF-8 with BOM first (utf-8-sig)
            # Use error handling to replace problematic characters
            try:
                upcoming_df = pd.read_csv(self.upcoming_file, encoding='utf-8-sig')
            except:
                try:
                    upcoming_df = pd.read_csv(self.upcoming_file, encoding='latin-1')
                except:
                    upcoming_df = pd.read_csv(self.upcoming_file, encoding='utf-8', encoding_errors='replace')

            # Clean column names
            upcoming_df.columns = upcoming_df.columns.str.strip()

            # Convert Date column to datetime - now standardized to YYYY-MM-DD format
            upcoming_df['Date'] = pd.to_datetime(upcoming_df['Date'], format='%Y-%m-%d', errors='coerce')
            current_date_obj = pd.to_datetime(current_date, format='%Y-%m-%d')

            # Filter for games that are on or after the current date
            upcoming_games = upcoming_df[upcoming_df['Date'] >= current_date_obj].copy()

            if upcoming_games.empty:
                return {
                    'error': 'No upcoming games found',
                    'current_date': current_date,
                    'total_games': 0,
                    'predictions': []
                }

            # Find the next round based on dates, not just round numbers
            # Get the earliest upcoming date
            earliest_upcoming_date = upcoming_games['Date'].min()

            # Find the round number of the earliest upcoming game
            earliest_round = upcoming_games[upcoming_games['Date'] == earliest_upcoming_date]['Round Number'].iloc[0]

            # Find all games in that round (they may be spread across multiple dates)
            next_round_games = upcoming_games[upcoming_games['Round Number'] == earliest_round]

            if next_round_games.empty:
                return {
                    'error': 'No games found for next round',
                    'current_date': current_date,
                    'total_games': 0,
                    'predictions': []
                }

            # Get the round number from the next round games
            next_round = next_round_games['Round Number'].iloc[0]

            # Convert to betting advisor format
            upcoming_games_list = []
            for _, game in next_round_games.iterrows():
                upcoming_games_list.append({
                    'home_team': game['Home Team'],
                    'away_team': game['Away Team'],
                    'match_date': game['Date'].strftime('%Y-%m-%d'),
                    'round_number': game['Round Number'],
                    'location': game['Location']
                })

            # Get betting recommendations
            recommendations = self.betting_advisor.get_betting_recommendations(
                upcoming_games_list, current_season=2025
            )

            # Calculate summary statistics
            total_games = len(recommendations)
            betting_opportunities = len([r for r in recommendations if r['recommendation']['bet_team']])
            avg_confidence = sum([r['recommendation']['confidence'] for r in recommendations if r['recommendation']['bet_team']]) / max(betting_opportunities, 1)

            return {
                'current_date': current_date,
                'next_round': int(next_round),
                'total_games': total_games,
                'betting_opportunities': betting_opportunities,
                'average_confidence': avg_confidence,
                'predictions': recommendations,
                'round_date': next_round_games['Date'].min().strftime('%d/%m/%Y') if not next_round_games.empty else 'Unknown'
            }

        except Exception as e:
            return {
                'error': f'Error processing upcoming games: {str(e)}',
                'current_date': current_date,
                'total_games': 0,
                'predictions': []
            }
