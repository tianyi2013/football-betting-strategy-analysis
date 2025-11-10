"""
Unified betting strategy application for all major European leagues
"""

import argparse
import os
import sys

# Add parent directory to path so imports work when running this script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.league_analytics import PremierLeagueAnalytics
from backtest.backtest_runner import BacktestRunner
from data_processing import cleanse_all_data
from predictions import run_predictions
from predictions.waterfall_betting_advisor import WaterfallBettingAdvisor
from strategies.form_strategy import FormStrategy
from strategies.home_away_strategy import HomeAwayStrategy
from strategies.momentum_strategy import MomentumStrategy
from strategies.top_bottom_strategy import TopBottomStrategy


class UnifiedBettingApp:
    """
    Unified application class that orchestrates all functionality for all major European leagues.
    """

    def __init__(self, league: str = "premier_league"):
        """
        Initialize the unified application.
        
        Args:
            league (str): League to analyze (premier_league, laliga_1, le_championnat, serie_a, bundesliga_1)
        """
        self.league = league
        self.data_directory = f"data/{league}"

        # Initialize components
        self.backtest_runner = BacktestRunner(self.data_directory)
        self.analytics = PremierLeagueAnalytics(self.data_directory)
        self.form_strategy = FormStrategy(self.data_directory)
        self.momentum_strategy = MomentumStrategy(self.data_directory)
        self.top_bottom_strategy = TopBottomStrategy(self.data_directory)
        self.home_away_strategy = HomeAwayStrategy(self.data_directory)

        # League display names
        self.league_names = {
            "premier_league": "Premier League",
            "laliga_1": "La Liga",
            "le_championnat": "Ligue 1",
            "serie_a": "Serie A",
            "bundesliga_1": "Bundesliga"
        }

        self.league_display = self.league_names.get(league, league.title())

    def run_league_analysis(self, season_year: int) -> None:
        """
        Run league analysis for a specific season.
        
        Args:
            season_year (int): Season year to analyze
        """
        print(f"Analyzing {self.league_display} {season_year}-{str(season_year + 1)[-2:]}")
        print("=" * 60)

        try:
            self.analytics.print_league_table(season_year)
        except Exception as e:
            print(f"Error analyzing season {season_year}: {e}")

    def run_backtest(self, top_n: int = 3, start_season: int = 2020,
                     end_season: int = 2024, home_away: bool = False) -> None:
        """
        Run backtest analysis for the specified parameters.
        
        Args:
            top_n (int): Number of top teams to analyze
            start_season (int): Starting season year
            end_season (int): Ending season year
            home_away (bool): Whether to use home-away strategy
        """
        print(f"[TROPHY] {self.league_display} Backtest Analysis")
        print("=" * 60)
        print(f"[CHART] Analyzing top {top_n} teams from {start_season} to {end_season}")
        print(f"[HOME] Home-Away Strategy: {'Yes' if home_away else 'No'}")
        print("=" * 60)

        try:
            if home_away:
                # Use home-away strategy
                results = self.home_away_strategy.analyze_betting_performance(
                    target_season=end_season,
                    odds_provider="bet365"
                )
            else:
                # Use top-bottom strategy
                results = self.top_bottom_strategy.analyze_betting_performance(
                    target_season=end_season,
                    top_n=top_n,
                    odds_provider="bet365"
                )

            if 'error' in results:
                print(f"[ERROR] Error: {results['error']}")
                return

            # Print results
            print(f"[TREND] Total Bets: {results['total_bets']}")
            print(f"[TARGET] Win Rate: {results['win_rate']:.1%}")
            print(f"[MONEY] ROI: {results['roi']:.1%}")
            print(f"[CASH] Profit/Loss: {results['profit_loss']:+.1f} units")
            print("=" * 60)

            if results['bet_details']:
                print("\n[DICE] BETTING DETAILS:")
                print("-" * 60)
                for bet in results['bet_details'][:10]:  # Show first 10 bets
                    print(f"[DATE] {bet['date']}: {bet['home_team']} vs {bet['away_team']}")
                    print(f"   [MONEY] Bet: {bet['bet_team']} @ {bet['odds']:.2f}")
                    print(f"   [TARGET] Result: {'WIN' if bet['result'] == 'win' else 'LOSS'} ({bet['profit_loss']:+.2f} units)")
                    print()

        except Exception as e:
            print(f"[ERROR] Error running backtest: {e}")

    def run_form_analysis(self, form_games: int = 5, form_threshold: float = 0.6,
                          start_season: int = 2020, end_season: int = 2024) -> None:
        """
        Run form-based betting analysis.
        
        Args:
            form_games (int): Number of games to consider for form
            form_threshold (float): Form threshold for betting
            start_season (int): Starting season year
            end_season (int): Ending season year
        """
        print(f"[CHART] {self.league_display} Form Analysis")
        print("=" * 60)
        print(f"[TARGET] Form Games: {form_games}")
        print(f"[TREND] Form Threshold: {form_threshold:.1%}")
        print(f"[DATE] Seasons: {start_season}-{end_season}")
        print("=" * 60)

        try:
            results = self.form_strategy.analyze_betting_performance(
                target_season=end_season,
                form_games=form_games,
                form_threshold=form_threshold,
                odds_provider="bet365"
            )

            if 'error' in results:
                print(f"[ERROR] Error: {results['error']}")
                return

            # Print results
            print(f"[TREND] Total Bets: {results['total_bets']}")
            print(f"[TARGET] Win Rate: {results['win_rate']:.1%}")
            print(f"[MONEY] ROI: {results['roi']:.1%}")
            print(f"[CASH] Profit/Loss: {results['profit_loss']:+.1f} units")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] Error running form analysis: {e}")

    def run_momentum_analysis(self, lookback_games: int = 5,
                              winning_momentum_threshold: float = 0.2,
                              start_season: int = 2020, end_season: int = 2024) -> None:
        """
        Run momentum-based betting analysis.
        
        Args:
            lookback_games (int): Number of games to look back for momentum
            winning_momentum_threshold (float): Momentum threshold for betting
            start_season (int): Starting season year
            end_season (int): Ending season year
        """
        print(f"[ROCKET] {self.league_display} Momentum Analysis")
        print("=" * 60)
        print(f"[TARGET] Lookback Games: {lookback_games}")
        print(f"[TREND] Momentum Threshold: {winning_momentum_threshold:.1%}")
        print(f"[DATE] Seasons: {start_season}-{end_season}")
        print("=" * 60)

        try:
            results = self.momentum_strategy.analyze_betting_performance(
                target_season=end_season,
                lookback_games=lookback_games,
                winning_momentum_threshold=winning_momentum_threshold,
                odds_provider="bet365"
            )

            if 'error' in results:
                print(f"[ERROR] Error: {results['error']}")
                return

            # Print results
            print(f"[TREND] Total Bets: {results['total_bets']}")
            print(f"[TARGET] Win Rate: {results['win_rate']:.1%}")
            print(f"[MONEY] ROI: {results['roi']:.1%}")
            print(f"[CASH] Profit/Loss: {results['profit_loss']:+.1f} units")
            print("=" * 60)

        except Exception as e:
            print(f"[ERROR] Error running momentum analysis: {e}")

    def run_predictions(self) -> None:
        """
        Run betting predictions for the next round of games using weighted approach.
        """
        print(f"[TARGET] {self.league_display} Betting Predictions (Weighted Approach)")
        print("=" * 60)
        print("Getting predictions for the next round of games...")
        print("=" * 60)

        try:
            run_predictions(self.league)
        except Exception as e:
            print(f"[ERROR] Error running predictions: {e}")

    def run_waterfall_advisor(self, bankroll: float = 1000.0,
                              risk_per_bet: float = 0.02) -> None:
        """
        Run waterfall betting advisor.
        
        Args:
            bankroll (float): Starting bankroll
            risk_per_bet (float): Risk per bet as percentage of bankroll
        """
        print(f"[WATER] {self.league_display} Waterfall Betting Advisor")
        print("=" * 60)
        print(f"[MONEY] Bankroll: ${bankroll:,.2f}")
        print(f"[TARGET] Risk per Bet: {risk_per_bet:.1%}")
        print("=" * 60)

        try:
            advisor = WaterfallBettingAdvisor(self.data_directory)
            advisor.run_advisor(bankroll, risk_per_bet)
        except Exception as e:
            print(f"[ERROR] Error running waterfall advisor: {e}")

    def cleanse_data(self) -> None:
        """
        Cleanse all data files.
        """
        print(f"[CLEANSE] {self.league_display} Data Cleansing")
        print("=" * 60)
        print("Cleansing all data files...")
        print("=" * 60)

        try:
            cleanse_all_data(self.data_directory)
            print("[SUCCESS] Data cleansing completed successfully!")
        except Exception as e:
            print(f"[ERROR] Error cleansing data: {e}")


def main():
    """Main function to run the unified application."""
    parser = argparse.ArgumentParser(description="Unified Betting Strategy Application")

    # League selection
    parser.add_argument('--league', type=str, default='premier_league',
                        choices=['premier_league', 'laliga_1', 'le_championnat', 'serie_a', 'bundesliga_1'],
                        help='League to analyze')

    # Command selection
    parser.add_argument('--command', type=str, required=True,
                        choices=['analyze', 'backtest', 'form', 'momentum', 'predict', 'waterfall', 'cleanse'],
                        help='Command to execute')

    # Backtest parameters
    parser.add_argument('--top-n', type=int, default=3,
                        help='Number of top teams for backtest (default: 3)')
    parser.add_argument('--start-season', type=int, default=2020,
                        help='Starting season year (default: 2020)')
    parser.add_argument('--end-season', type=int, default=2024,
                        help='Ending season year (default: 2024)')
    parser.add_argument('--home-away', action='store_true',
                        help='Use home-away strategy instead of top-bottom')

    # Form analysis parameters
    parser.add_argument('--form-games', type=int, default=5,
                        help='Number of games for form analysis (default: 5)')
    parser.add_argument('--form-threshold', type=float, default=0.6,
                        help='Form threshold for betting (default: 0.6)')

    # Momentum analysis parameters
    parser.add_argument('--lookback-games', type=int, default=5,
                        help='Number of games to look back for momentum (default: 5)')
    parser.add_argument('--winning-momentum-threshold', type=float, default=0.2,
                        help='Momentum threshold for betting (default: 0.2)')

    # Waterfall advisor parameters
    parser.add_argument('--bankroll', type=float, default=1000.0,
                        help='Starting bankroll for waterfall advisor (default: 1000.0)')
    parser.add_argument('--risk-per-bet', type=float, default=0.02,
                        help='Risk per bet as percentage of bankroll (default: 0.02)')

    args = parser.parse_args()

    # Initialize application
    app = UnifiedBettingApp(args.league)

    # Execute command
    try:
        if args.command == 'analyze':
            app.run_league_analysis(args.end_season)
        elif args.command == 'backtest':
            app.run_backtest(args.top_n, args.start_season, args.end_season, args.home_away)
        elif args.command == 'form':
            app.run_form_analysis(args.form_games, args.form_threshold, args.start_season, args.end_season)
        elif args.command == 'momentum':
            app.run_momentum_analysis(args.lookback_games, args.winning_momentum_threshold, args.start_season, args.end_season)
        elif args.command == 'predict':
            app.run_predictions()
        elif args.command == 'waterfall':
            app.run_waterfall_advisor(args.bankroll, args.risk_per_bet)
        elif args.command == 'cleanse':
            app.cleanse_data()
        else:
            print(f"[ERROR] Unknown command: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n[GOODBYE] Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
