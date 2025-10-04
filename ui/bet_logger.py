#!/usr/bin/env python3
"""
Comprehensive Bet Logger for Football Betting
Handles bet recommendations, odds input, and automatic P&L calculation
"""

import pandas as pd
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import sys

class BetLogger:
    """Comprehensive bet logging system for football betting"""
    
    def __init__(self, data_file: str = "bet_log.json"):
        self.data_file = data_file
        self.bets = self._load_bets()
        self.leagues = ['premier_league', 'bundesliga_1', 'laliga_1', 'le_championnat', 'serie_a']
        
    def _load_bets(self) -> List[Dict]:
        """Load existing bets from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_bets(self):
        """Save bets to JSON file"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.bets, f, indent=2, ensure_ascii=False)
    
    def get_next_round_recommendations(self) -> Dict[str, List[Dict]]:
        """Get betting recommendations for next round from all leagues"""
        print("🎯 COLLECTING BETTING RECOMMENDATIONS FROM ALL LEAGUES")
        print("=" * 60)
        
        all_recommendations = {}
        
        for league in self.leagues:
            print(f"\n🏆 Processing {league.upper().replace('_', ' ')}:")
            
            try:
                # Import and run prediction system
                from app.unified_app import UnifiedBettingApp
                
                app = UnifiedBettingApp()
                app.league = league
                app.league_display = league.replace('_', ' ').title()
                
                # Get predictions
                predictions = app.get_next_round_predictions()
                
                if predictions:
                    # Filter for betting opportunities
                    betting_opportunities = []
                    for prediction in predictions:
                        if prediction.get('recommendation', {}).get('bet_team'):
                            betting_opportunities.append(prediction)
                    
                    all_recommendations[league] = betting_opportunities
                    print(f"  ✅ Found {len(betting_opportunities)} betting opportunities")
                else:
                    all_recommendations[league] = []
                    print(f"  ⚠️  No predictions available")
                    
            except Exception as e:
                print(f"  ❌ Error getting predictions: {e}")
                all_recommendations[league] = []
        
        return all_recommendations
    
    def display_recommendations(self, recommendations: Dict[str, List[Dict]]):
        """Display all betting recommendations in a formatted way"""
        print("\n" + "=" * 80)
        print("📋 BETTING RECOMMENDATIONS FOR NEXT ROUND")
        print("=" * 80)
        
        total_opportunities = 0
        
        for league, bets in recommendations.items():
            if bets:
                print(f"\n🏆 {league.upper().replace('_', ' ')}:")
                print("-" * 50)
                
                for i, bet in enumerate(bets, 1):
                    rec = bet['recommendation']
                    print(f"  {i}. {bet['game']}")
                    print(f"     💰 Bet: {rec['bet_team']} ({rec['bet_type']})")
                    print(f"     📊 Confidence: {rec['confidence']*100:.1f}%")
                    print(f"     🎯 Strategy: {rec.get('strategy', 'Unknown')}")
                    print()
                    total_opportunities += 1
        
        print(f"\n📊 TOTAL OPPORTUNITIES: {total_opportunities}")
        return total_opportunities
    
    def add_bet_with_odds(self, league: str, game: str, bet_team: str, bet_type: str, 
                         confidence: float, strategy: str, stake: float, odds: float):
        """Add a bet with user-provided odds"""
        bet_id = f"BET_{len(self.bets) + 1:04d}"
        
        bet_entry = {
            "bet_id": bet_id,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "league": league,
            "game": game,
            "bet_team": bet_team,
            "bet_type": bet_type,
            "confidence": confidence,
            "strategy": strategy,
            "stake": stake,
            "odds": odds,
            "potential_return": stake * odds,
            "potential_profit": stake * (odds - 1),
            "status": "PENDING",
            "result": None,
            "actual_return": None,
            "profit_loss": None,
            "notes": ""
        }
        
        self.bets.append(bet_entry)
        self._save_bets()
        
        print(f"✅ Bet added: {bet_id}")
        print(f"   Game: {game}")
        print(f"   Bet: {bet_team} @ {odds}")
        print(f"   Stake: £{stake}")
        print(f"   Potential Return: £{bet_entry['potential_return']:.2f}")
        print(f"   Potential Profit: £{bet_entry['potential_profit']:.2f}")
        
        return bet_id
    
    def update_bet_result(self, bet_id: str, result: str, actual_score: str = None):
        """Update bet result after match completion"""
        bet = next((b for b in self.bets if b['bet_id'] == bet_id), None)
        
        if not bet:
            print(f"❌ Bet {bet_id} not found")
            return False
        
        if bet['status'] != 'PENDING':
            print(f"❌ Bet {bet_id} already has result: {bet['status']}")
            return False
        
        # Calculate P&L based on result
        if result.upper() == 'WON':
            bet['status'] = 'WON'
            bet['result'] = 'WON'
            bet['actual_return'] = bet['potential_return']
            bet['profit_loss'] = bet['potential_profit']
        elif result.upper() == 'LOST':
            bet['status'] = 'LOST'
            bet['result'] = 'LOST'
            bet['actual_return'] = 0
            bet['profit_loss'] = -bet['stake']
        elif result.upper() == 'VOID':
            bet['status'] = 'VOID'
            bet['result'] = 'VOID'
            bet['actual_return'] = bet['stake']
            bet['profit_loss'] = 0
        else:
            print(f"❌ Invalid result: {result}. Use WON, LOST, or VOID")
            return False
        
        if actual_score:
            bet['notes'] = f"Final Score: {actual_score}"
        
        self._save_bets()
        
        print(f"✅ Bet {bet_id} updated:")
        print(f"   Result: {bet['result']}")
        print(f"   P&L: £{bet['profit_loss']:.2f}")
        
        return True
    
    def calculate_round_pnl(self, league: str = None) -> Dict:
        """Calculate P&L for a specific round or all leagues"""
        if league:
            league_bets = [b for b in self.bets if b['league'] == league and b['status'] != 'PENDING']
        else:
            league_bets = [b for b in self.bets if b['status'] != 'PENDING']
        
        if not league_bets:
            return {
                'total_bets': 0,
                'total_stake': 0,
                'total_return': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'roi': 0
            }
        
        total_bets = len(league_bets)
        total_stake = sum(b['stake'] for b in league_bets)
        total_return = sum(b['actual_return'] for b in league_bets)
        total_pnl = sum(b['profit_loss'] for b in league_bets)
        
        won_bets = len([b for b in league_bets if b['result'] == 'WON'])
        win_rate = (won_bets / total_bets) * 100 if total_bets > 0 else 0
        roi = (total_pnl / total_stake) * 100 if total_stake > 0 else 0
        
        return {
            'total_bets': total_bets,
            'total_stake': total_stake,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'roi': roi
        }
    
    def display_performance_summary(self, league: str = None):
        """Display performance summary"""
        stats = self.calculate_round_pnl(league)
        
        print("\n" + "=" * 60)
        if league:
            print(f"📊 PERFORMANCE SUMMARY - {league.upper().replace('_', ' ')}")
        else:
            print("📊 OVERALL PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"📈 Total Bets: {stats['total_bets']}")
        print(f"💰 Total Stake: £{stats['total_stake']:.2f}")
        print(f"🎯 Win Rate: {stats['win_rate']:.1f}%")
        print(f"💵 Total Return: £{stats['total_return']:.2f}")
        print(f"📊 Total P&L: £{stats['total_pnl']:.2f}")
        print(f"📈 ROI: {stats['roi']:.1f}%")
        
        if stats['total_pnl'] > 0:
            print("🎉 PROFITABLE ROUND! 🎉")
        elif stats['total_pnl'] < 0:
            print("📉 Loss this round")
        else:
            print("⚖️ Break even")
    
    def get_pending_bets(self) -> List[Dict]:
        """Get all pending bets"""
        return [b for b in self.bets if b['status'] == 'PENDING']
    
    def display_pending_bets(self):
        """Display all pending bets"""
        pending = self.get_pending_bets()
        
        if not pending:
            print("✅ No pending bets")
            return
        
        print("\n" + "=" * 60)
        print("⏳ PENDING BETS")
        print("=" * 60)
        
        for bet in pending:
            print(f"\n🎯 {bet['bet_id']}:")
            print(f"   Game: {bet['game']}")
            print(f"   Bet: {bet['bet_team']} @ {bet['odds']}")
            print(f"   Stake: £{bet['stake']}")
            print(f"   League: {bet['league']}")
            print(f"   Strategy: {bet['strategy']}")
    
    def export_to_csv(self, filename: str = None):
        """Export all bets to CSV"""
        if not filename:
            filename = f"bet_log_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not self.bets:
            print("❌ No bets to export")
            return
        
        df = pd.DataFrame(self.bets)
        df.to_csv(filename, index=False)
        print(f"✅ Bets exported to {filename}")
    
    def interactive_bet_entry(self):
        """Interactive bet entry system"""
        print("\n🎯 INTERACTIVE BET ENTRY")
        print("=" * 40)
        
        # Get recommendations
        recommendations = self.get_next_round_recommendations()
        
        if not any(recommendations.values()):
            print("❌ No betting recommendations available")
            return
        
        # Display recommendations
        total_opportunities = self.display_recommendations(recommendations)
        
        if total_opportunities == 0:
            print("❌ No betting opportunities found")
            return
        
        print("\n" + "=" * 60)
        print("💰 BET ENTRY SYSTEM")
        print("=" * 60)
        
        # Collect bets from user
        entered_bets = []
        
        for league, bets in recommendations.items():
            if not bets:
                continue
            
            print(f"\n🏆 {league.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            for i, bet in enumerate(bets, 1):
                rec = bet['recommendation']
                
                print(f"\n{i}. {bet['game']}")
                print(f"   Recommended: {rec['bet_team']} ({rec['bet_type']})")
                print(f"   Confidence: {rec['confidence']*100:.1f}%")
                print(f"   Strategy: {rec.get('strategy', 'Unknown')}")
                
                choice = input(f"\n   🤔 Enter this bet? (y/n): ").lower().strip()
                
                if choice == 'y':
                    try:
                        stake = float(input("   💰 Enter stake amount: £"))
                        odds = float(input("   📊 Enter odds (e.g., 2.5): "))
                        
                        bet_id = self.add_bet_with_odds(
                            league=league,
                            game=bet['game'],
                            bet_team=rec['bet_team'],
                            bet_type=rec['bet_type'],
                            confidence=rec['confidence'],
                            strategy=rec.get('strategy', 'Unknown'),
                            stake=stake,
                            odds=odds
                        )
                        
                        entered_bets.append(bet_id)
                        
                    except ValueError:
                        print("   ❌ Invalid input, skipping this bet")
                    except Exception as e:
                        print(f"   ❌ Error adding bet: {e}")
        
        print(f"\n✅ Successfully entered {len(entered_bets)} bets")
        return entered_bets

def main():
    """Main function for bet logger"""
    logger = BetLogger()
    
    print("🎲 COMPREHENSIVE BET LOGGER")
    print("=" * 50)
    print("1. Get next round recommendations")
    print("2. Enter bets with odds")
    print("3. Update bet results")
    print("4. View performance summary")
    print("5. View pending bets")
    print("6. Export to CSV")
    print("7. Interactive bet entry")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\n🎯 Choose option (0-7): ").strip()
            
            if choice == '0':
                print("👋 Goodbye!")
                break
            elif choice == '1':
                recommendations = logger.get_next_round_recommendations()
                logger.display_recommendations(recommendations)
            elif choice == '2':
                print("\n📝 Manual bet entry:")
                league = input("League: ").strip()
                game = input("Game: ").strip()
                bet_team = input("Bet Team: ").strip()
                bet_type = input("Bet Type: ").strip()
                confidence = float(input("Confidence (0-1): "))
                strategy = input("Strategy: ").strip()
                stake = float(input("Stake: £"))
                odds = float(input("Odds: "))
                
                logger.add_bet_with_odds(league, game, bet_team, bet_type, confidence, strategy, stake, odds)
            elif choice == '3':
                bet_id = input("Bet ID: ").strip()
                result = input("Result (WON/LOST/VOID): ").strip()
                score = input("Final Score (optional): ").strip() or None
                logger.update_bet_result(bet_id, result, score)
            elif choice == '4':
                league = input("League (or press Enter for all): ").strip() or None
                logger.display_performance_summary(league)
            elif choice == '5':
                logger.display_pending_bets()
            elif choice == '6':
                filename = input("Filename (or press Enter for auto): ").strip() or None
                logger.export_to_csv(filename)
            elif choice == '7':
                logger.interactive_bet_entry()
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
