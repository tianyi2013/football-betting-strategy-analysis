#!/usr/bin/env python3
"""
Prediction Runner: Main entry point for getting betting predictions.
This consolidates the functionality from get_predictions.py.
"""

from .next_round_predictor import NextRoundPredictor
from datetime import datetime

def run_predictions(league: str = "premier_league"):
    """Get predictions for the next round of games.
    
    Args:
        league (str): League name - "premier_league", "laliga_1", "le_championnat", "serie_a", or "bundesliga_1"
    """
    
    # Map league names to display names and data directories
    league_info = {
        "premier_league": {
            "display_name": "Premier League",
            "data_dir": "data/premier_league"
        },
        "laliga_1": {
            "display_name": "La Liga",
            "data_dir": "data/laliga_1"
        },
        "le_championnat": {
            "display_name": "Ligue 1",
            "data_dir": "data/le_championnat"
        },
        "serie_a": {
            "display_name": "Serie A",
            "data_dir": "data/serie_a"
        },
        "bundesliga_1": {
            "display_name": "Bundesliga",
            "data_dir": "data/bundesliga_1"
        }
    }
    
    if league not in league_info:
        print(f"❌ Error: Unknown league '{league}'. Supported leagues: {list(league_info.keys())}")
        return
    
    league_display = league_info[league]["display_name"]
    data_dir = league_info[league]["data_dir"]
    
    print(f"🎯 {league_display.upper()} BETTING PREDICTOR")
    print("=" * 60)
    print("Loading upcoming games and calculating predictions...")
    print("=" * 60)
    
    # Initialize predictor with league-specific data directory
    predictor = NextRoundPredictor(data_dir)
    
    # Get current date
    current_date = datetime.now().strftime('%d/%m/%Y')
    print(f"📅 Current Date: {current_date}")
    
    # Get predictions for next round
    result = predictor.get_next_round_predictions(current_date)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Print results
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
    print("=" * 60)
    print("\n💡 Note: Predictions are only for the next round.")
    print("   After each round, update your data and run predictions again")
    print("   to get fresh recommendations based on the latest results.")

def main():
    """Main function to run predictions."""
    try:
        run_predictions()
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
