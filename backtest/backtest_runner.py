"""
Backtest runner for executing and managing backtests
"""

from typing import Dict, List

from strategies.home_away_strategy import HomeAwayStrategy
from strategies.top_bottom_strategy import TopBottomStrategy


class BacktestRunner:
    """
    Runs backtests for different strategies and parameters.
    """
    
    def __init__(self, data_directory: str = "data/premier_league"):
        """
        Initialize the backtest runner.
        
        Args:
            data_directory (str): Path to directory containing season CSV files
        """
        self.data_directory = data_directory
        self.top_bottom_strategy = TopBottomStrategy(data_directory)
        self.home_away_strategy = HomeAwayStrategy(data_directory)
    
    def run_single_backtest(self, top_n: int, start_season: int = None, 
                           end_season: int = None, include_against_bottom: bool = True,
                           odds_provider: str = "bet365") -> Dict:
        """
        Run a single backtest with specified parameters.
        
        Args:
            top_n (int): Number of top teams to bet on
            start_season (int, optional): Starting season for backtest
            end_season (int, optional): Ending season for backtest
            include_against_bottom (bool): Whether to include betting against bottom teams
            
        Returns:
            Dict: Backtest results
        """
        return self.top_bottom_strategy.backtest_strategy(
            top_n=top_n,
            start_season=start_season,
            end_season=end_season,
            include_against_bottom=include_against_bottom,
            odds_provider=odds_provider
        )
    
    def run_multiple_backtests(self, n_values: List[int], start_season: int = None, 
                              end_season: int = None, include_against_bottom: bool = True,
                              odds_provider: str = "bet365") -> Dict:
        """
        Run multiple backtests with different N values.
        
        Args:
            n_values (List[int]): List of N values to test
            start_season (int, optional): Starting season for backtest
            end_season (int, optional): Ending season for backtest
            include_against_bottom (bool): Whether to include betting against bottom teams
            
        Returns:
            Dict: Results for all N values
        """
        results = {}
        
        for n in n_values:
            print(f"Running backtest for N={n}...")
            backtest_result = self.run_single_backtest(
                top_n=n,
                start_season=start_season,
                end_season=end_season,
                include_against_bottom=include_against_bottom,
                odds_provider=odds_provider
            )
            results[f"n_{n}"] = backtest_result
        
        return results
    
    def compare_strategies(self, top_n: int, start_season: int = None, 
                          end_season: int = None, odds_provider: str = "bet365") -> Dict:
        """
        Compare FOR-only vs FOR+AGAINST strategies.
        
        Args:
            top_n (int): Number of top teams to bet on
            start_season (int, optional): Starting season for backtest
            end_season (int, optional): Ending season for backtest
            
        Returns:
            Dict: Comparison results
        """
        # Run FOR-only strategy
        for_only_result = self.run_single_backtest(
            top_n=top_n,
            start_season=start_season,
            end_season=end_season,
            include_against_bottom=False,
            odds_provider=odds_provider
        )
        
        # Run FOR+AGAINST strategy
        enhanced_result = self.run_single_backtest(
            top_n=top_n,
            start_season=start_season,
            end_season=end_season,
            include_against_bottom=True,
            odds_provider=odds_provider
        )
        
        return {
            'for_only': for_only_result,
            'enhanced': enhanced_result,
            'comparison': self._calculate_comparison(for_only_result, enhanced_result)
        }
    
    def _calculate_comparison(self, for_only_result: Dict, enhanced_result: Dict) -> Dict:
        """
        Calculate comparison metrics between two strategies.
        
        Args:
            for_only_result (Dict): FOR-only strategy results
            enhanced_result (Dict): Enhanced strategy results
            
        Returns:
            Dict: Comparison metrics
        """
        if 'error' in for_only_result or 'error' in enhanced_result:
            return {'error': 'Cannot compare due to errors in results'}
        
        for_only_overall = for_only_result['overall']
        enhanced_overall = enhanced_result['overall']
        
        return {
            'additional_bets': enhanced_overall['total_bets'] - for_only_overall['total_bets'],
            'win_rate_change': enhanced_overall['win_rate'] - for_only_overall['win_rate'],
            'roi_change': enhanced_overall['roi'] - for_only_overall['roi'],
            'profit_change': enhanced_overall['profit_loss'] - for_only_overall['profit_loss']
        }
    
    def run_home_away_backtest(self, start_season: int = None, 
                              end_season: int = None, odds_provider: str = "bet365") -> Dict:
        """
        Run backtest for the home-away strategy.
        
        Args:
            start_season (int, optional): Starting season for backtest
            end_season (int, optional): Ending season for backtest
            odds_provider (str): Odds provider to use
            
        Returns:
            Dict: Home-away backtest results
        """
        return self.home_away_strategy.backtest_strategy(
            start_season=start_season,
            end_season=end_season,
            odds_provider=odds_provider
        )
