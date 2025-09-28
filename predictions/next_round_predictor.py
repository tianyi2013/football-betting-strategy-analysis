#!/usr/bin/env python3
"""
Next Round Predictor: Reads upcoming games from CSV and provides betting predictions
for the next round of games that haven't been played yet.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
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
        
        # Try different upcoming file naming conventions
        import os
        upcoming_files = [
            f"{data_directory}/upcoming_25.csv",
            f"{data_directory}/upcoming_2025.csv"
        ]
        
        self.upcoming_file = None
        for file_path in upcoming_files:
            if os.path.exists(file_path):
                self.upcoming_file = file_path
                break
        
        if self.upcoming_file is None:
            # Default to upcoming_25.csv if none found
            self.upcoming_file = f"{data_directory}/upcoming_25.csv"
        
        self.results_file = f"{data_directory}/2025.csv"
    
    def get_next_round_predictions(self, current_date: str = None) -> Dict:
        """
        Get betting predictions for the next round of upcoming games.
        
        Args:
            current_date (str): Current date in format 'DD/MM/YYYY' (default: today)
            
        Returns:
            Dict: Predictions for the next round with metadata
        """
        if current_date is None:
            current_date = datetime.now().strftime('%d/%m/%Y')
        
        try:
            # Load upcoming games
            upcoming_df = pd.read_csv(self.upcoming_file)
            
            # Clean column names
            upcoming_df.columns = upcoming_df.columns.str.strip()
            
            # Convert Date column to datetime - now standardized to YYYY-MM-DD format
            upcoming_df['Date'] = pd.to_datetime(upcoming_df['Date'], format='%Y-%m-%d', errors='coerce')
            current_date_obj = pd.to_datetime(current_date, format='%d/%m/%Y')
            
            # Filter for games that haven't been played yet (no result or future date)
            upcoming_games = upcoming_df[
                (upcoming_df['Date'] > current_date_obj) | 
                (upcoming_df['Result'].isna() | (upcoming_df['Result'] == ''))
            ].copy()
            
            if upcoming_games.empty:
                return {
                    'error': 'No upcoming games found',
                    'current_date': current_date,
                    'total_games': 0,
                    'predictions': []
                }
            
            # Group by round to find the next round
            rounds = upcoming_games['Round Number'].unique()
            next_round = min(rounds)
            
            # Get games for the next round
            next_round_games = upcoming_games[upcoming_games['Round Number'] == next_round]
            
            if next_round_games.empty:
                return {
                    'error': 'No games found for next round',
                    'current_date': current_date,
                    'next_round': next_round,
                    'total_games': 0,
                    'predictions': []
                }
            
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
    
    
    def print_next_round_predictions(self, current_date: str = None):
        """
        Print formatted predictions for the next round.
        
        Args:
            current_date (str): Current date in format 'DD/MM/YYYY' (default: today)
        """
        result = self.get_next_round_predictions(current_date)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print("🎯 NEXT ROUND BETTING PREDICTIONS")
        print("=" * 60)
        print(f"📅 Current Date: {result['current_date']}")
        print(f"🏆 Next Round: {result['next_round']}")
        print(f"📊 Total Games: {result['total_games']}")
        print(f"💰 Betting Opportunities: {result['betting_opportunities']}")
        print(f"🎯 Average Confidence: {result['average_confidence']:.1%}")
        print(f"📅 Round Date: {result['round_date']}")
        print("=" * 60)
        
        if result['predictions']:
            print("\n🎲 BETTING RECOMMENDATIONS:")
            print("-" * 60)
            
            for i, pred in enumerate(result['predictions'], 1):
                game = pred['game']
                recommendation = pred['recommendation']
                individual_strategies = pred['individual_strategies']
                bet_team = recommendation['bet_team']
                confidence = recommendation['confidence']
                reason = recommendation['reason']
                
                print(f"{i:2d}. {game}")
                print("    " + "="*50)
                
                # Show detailed analysis for each strategy
                print("    📊 STRATEGY ANALYSIS:")
                
                # Momentum Strategy
                momentum = individual_strategies['momentum']
                print(f"    🏆 Momentum: {momentum['bet_team'] or 'None'} (Confidence: {momentum['confidence']:.1%})")
                print(f"        {momentum['reason']}")
                if 'detailed_reason' in momentum:
                    print(f"        📊 Details: {momentum['detailed_reason']}")
                
                # Form Strategy  
                form = individual_strategies['form']
                print(f"    🥈 Form: {form['bet_team'] or 'None'} (Confidence: {form['confidence']:.1%})")
                print(f"        {form['reason']}")
                if 'detailed_reason' in form:
                    print(f"        📊 Details: {form['detailed_reason']}")
                
                # Top-Bottom Strategy
                top_bottom = individual_strategies['top_bottom']
                print(f"    🥉 Top-Bottom: {top_bottom['bet_team'] or 'None'} (Confidence: {top_bottom['confidence']:.1%})")
                print(f"        {top_bottom['reason']}")
                if 'detailed_reason' in top_bottom:
                    print(f"        📊 Details: {top_bottom['detailed_reason']}")
                
                # Home-Away Strategy
                home_away = individual_strategies['home_away']
                print(f"    🏠 Home-Away: {home_away['bet_team'] or 'None'} (Confidence: {home_away['confidence']:.1%})")
                print(f"        {home_away['reason']}")
                
                # Final recommendation
                print(f"    🎯 FINAL RECOMMENDATION:")
                if bet_team:
                    print(f"        💰 BET ON: {bet_team}")
                    print(f"        🎯 Confidence: {confidence:.1%}")
                    print(f"        📝 Reason: {reason}")
                    if recommendation['supporting_strategies']:
                        print(f"        🔍 Supporting: {', '.join(recommendation['supporting_strategies'])}")
                else:
                    print(f"        ❌ No bet recommended")
                    print(f"        📝 Reason: {reason}")
                
                print()
        else:
            print("No predictions available.")
        
        print("=" * 60)
        print("⚠️  Remember: These are recommendations based on historical data.")
        print("   Always do your own research and bet responsibly!")


def main():
    """Main function to run the next round predictor."""
    predictor = NextRoundPredictor()
    
    print("🎯 PREMIER LEAGUE BETTING PREDICTOR")
    print("=" * 60)
    print("Getting predictions for the next round of games...")
    print("=" * 60)
    
    try:
        predictor.print_next_round_predictions()
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
