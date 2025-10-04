#!/usr/bin/env python3
"""
Automatic P&L Calculator
Automatically calculates bet results when data files are updated
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from bet_logger import BetLogger

class AutoPNLCalculator:
    """Automatically calculates P&L when data files are updated"""
    
    def __init__(self):
        self.logger = BetLogger()
        self.leagues = ['premier_league', 'bundesliga_1', 'laliga_1', 'le_championnat', 'serie_a']
    
    def get_match_results(self, league: str) -> Dict[str, Dict]:
        """Get match results from updated data files"""
        try:
            # Read the updated 2025.csv file
            csv_file = f"data/{league}/2025.csv"
            if not os.path.exists(csv_file):
                return {}
            
            df = pd.read_csv(csv_file)
            
            # Get the most recent matches (last few rows)
            recent_matches = df.tail(10)  # Get last 10 matches
            
            results = {}
            for _, match in recent_matches.iterrows():
                # Create match key
                home_team = match.get('HomeTeam', '')
                away_team = match.get('AwayTeam', '')
                match_key = f"{home_team} vs {away_team}"
                
                # Get result
                home_score = match.get('FTHG', 0)
                away_score = match.get('FTAG', 0)
                
                # Determine winner
                if home_score > away_score:
                    winner = home_team
                elif away_score > home_score:
                    winner = away_team
                else:
                    winner = 'Draw'
                
                results[match_key] = {
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'winner': winner,
                    'score': f"{home_score}-{away_score}"
                }
            
            return results
            
        except Exception as e:
            print(f"❌ Error reading match results for {league}: {e}")
            return {}
    
    def calculate_bet_result(self, bet: Dict, match_results: Dict[str, Dict]) -> Optional[str]:
        """Calculate the result of a single bet"""
        try:
            # Find matching game in results
            game = bet['game']
            
            # Try different variations of the game name
            possible_keys = [
                game,
                game.replace(' vs ', ' v '),
                game.replace(' vs ', ' - '),
                game.replace(' vs ', ' vs. ')
            ]
            
            match_result = None
            for key in possible_keys:
                if key in match_results:
                    match_result = match_results[key]
                    break
            
            if not match_result:
                # Try to find by team names
                bet_team = bet['bet_team']
                for match_key, result in match_results.items():
                    if bet_team in match_key:
                        match_result = result
                        break
            
            if not match_result:
                return None
            
            # Determine bet result based on bet type and match outcome
            bet_type = bet['bet_type'].upper()
            winner = match_result['winner']
            bet_team = bet['bet_team']
            
            if bet_type in ['WIN', 'HOME_WIN', 'AWAY_WIN']:
                if bet_type == 'WIN' and winner == bet_team:
                    return 'WON'
                elif bet_type == 'HOME_WIN' and winner == match_result['home_team']:
                    return 'WON'
                elif bet_type == 'AWAY_WIN' and winner == match_result['away_team']:
                    return 'WON'
                else:
                    return 'LOST'
            
            elif bet_type == 'DRAW':
                if winner == 'Draw':
                    return 'WON'
                else:
                    return 'LOST'
            
            elif bet_type in ['OVER', 'UNDER']:
                # For over/under bets, we'd need total goals
                # This is a simplified version
                total_goals = match_result['home_score'] + match_result['away_score']
                if bet_type == 'OVER' and total_goals > 2.5:  # Assuming 2.5 line
                    return 'WON'
                elif bet_type == 'UNDER' and total_goals < 2.5:
                    return 'WON'
                else:
                    return 'LOST'
            
            else:
                # Default logic for other bet types
                if winner == bet_team:
                    return 'WON'
                else:
                    return 'LOST'
                
        except Exception as e:
            print(f"❌ Error calculating bet result: {e}")
            return None
    
    def update_pending_bets(self, league: str = None):
        """Update all pending bets for a league or all leagues"""
        print(f"🔄 UPDATING PENDING BETS FOR {league.upper() if league else 'ALL LEAGUES'}")
        print("=" * 60)
        
        # Get pending bets
        pending_bets = self.logger.get_pending_bets()
        
        if league:
            pending_bets = [b for b in pending_bets if b['league'] == league]
        
        if not pending_bets:
            print("✅ No pending bets to update")
            return
        
        print(f"📊 Found {len(pending_bets)} pending bets")
        
        # Get match results for each league
        all_results = {}
        leagues_to_check = [league] if league else self.leagues
        
        for lg in leagues_to_check:
            results = self.get_match_results(lg)
            if results:
                all_results[lg] = results
                print(f"  ✅ {lg}: {len(results)} match results found")
            else:
                print(f"  ⚠️  {lg}: No recent match results")
        
        # Update each pending bet
        updated_count = 0
        
        for bet in pending_bets:
            bet_league = bet['league']
            
            if bet_league in all_results:
                match_results = all_results[bet_league]
                result = self.calculate_bet_result(bet, match_results)
                
                if result:
                    # Update the bet
                    success = self.logger.update_bet_result(
                        bet['bet_id'], 
                        result, 
                        f"Auto-calculated from {bet_league} data"
                    )
                    
                    if success:
                        updated_count += 1
                        print(f"  ✅ {bet['bet_id']}: {result}")
                    else:
                        print(f"  ❌ {bet['bet_id']}: Update failed")
                else:
                    print(f"  ⚠️  {bet['bet_id']}: No matching game found")
            else:
                print(f"  ⚠️  {bet['bet_id']}: No results for {bet_league}")
        
        print(f"\n📊 Updated {updated_count} out of {len(pending_bets)} pending bets")
        
        if updated_count > 0:
            # Show performance summary
            self.logger.display_performance_summary(league)
    
    def check_data_updates(self):
        """Check if data files have been updated and update bets accordingly"""
        print("🔍 CHECKING FOR DATA UPDATES")
        print("=" * 40)
        
        # Check each league for updates
        for league in self.leagues:
            csv_file = f"data/{league}/2025.csv"
            if os.path.exists(csv_file):
                # Get file modification time
                mod_time = os.path.getmtime(csv_file)
                mod_date = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                
                print(f"📁 {league}: Last updated {mod_date}")
                
                # Check if there are pending bets for this league
                pending_bets = [b for b in self.logger.get_pending_bets() if b['league'] == league]
                
                if pending_bets:
                    print(f"  ⏳ {len(pending_bets)} pending bets found")
                    
                    # Ask user if they want to update
                    choice = input(f"  🤔 Update bets for {league}? (y/n): ").lower().strip()
                    if choice == 'y':
                        self.update_pending_bets(league)
                else:
                    print(f"  ✅ No pending bets for {league}")
            else:
                print(f"  ❌ {league}: Data file not found")
    
    def auto_update_all(self):
        """Automatically update all pending bets"""
        print("🤖 AUTOMATIC P&L UPDATE")
        print("=" * 40)
        
        for league in self.leagues:
            pending_bets = [b for b in self.logger.get_pending_bets() if b['league'] == league]
            
            if pending_bets:
                print(f"\n🏆 Updating {league}:")
                self.update_pending_bets(league)
            else:
                print(f"✅ {league}: No pending bets")

def main():
    """Main function for auto P&L calculator"""
    calculator = AutoPNLCalculator()
    
    print("🤖 AUTOMATIC P&L CALCULATOR")
    print("=" * 50)
    print("1. Check for data updates")
    print("2. Update pending bets for specific league")
    print("3. Update all pending bets")
    print("4. View current performance")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\n🎯 Choose option (0-4): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                calculator.check_data_updates()
            elif choice == '2':
                league = input("Enter league name: ").strip()
                if league in calculator.leagues:
                    calculator.update_pending_bets(league)
                else:
                    print(f"❌ Invalid league. Choose from: {', '.join(calculator.leagues)}")
            elif choice == '3':
                calculator.auto_update_all()
            elif choice == '4':
                league = input("League (or press Enter for all): ").strip() or None
                calculator.logger.display_performance_summary(league)
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
