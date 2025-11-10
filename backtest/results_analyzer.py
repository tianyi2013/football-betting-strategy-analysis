"""
Results analyzer for backtest results
"""

from typing import Dict, List

import pandas as pd

from analytics.performance_metrics import PerformanceMetrics


class ResultsAnalyzer:
    """
    Analyzes and visualizes backtest results.
    """
    
    @staticmethod
    def create_yearly_table(season_results: List[Dict]) -> pd.DataFrame:
        """
        Create a detailed yearly table from season results.
        
        Args:
            season_results (List[Dict]): List of season results
            
        Returns:
            pd.DataFrame: Yearly analysis table
        """
        table_data = []
        
        # Get top_n from the first result (all should have the same value)
        top_n = season_results[0]['top_n'] if season_results else 3
        
        for result in season_results:
            # Separate FOR and AGAINST bets
            for_bets = [bet for bet in result['bet_details'] if bet['bet_type'] == 'FOR']
            against_bets = [bet for bet in result['bet_details'] if bet['bet_type'] == 'AGAINST']
            
            # Calculate metrics
            for_metrics = PerformanceMetrics.calculate_metrics(for_bets)
            against_metrics = PerformanceMetrics.calculate_metrics(against_bets)
            
            # Overall metrics
            total_bets = for_metrics['total_bets'] + against_metrics['total_bets']
            total_wins = for_metrics['winning_bets'] + against_metrics['winning_bets']
            overall_win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
            total_stake = for_metrics['total_stake'] + against_metrics['total_stake']
            total_winnings = for_metrics['total_winnings'] + against_metrics['total_winnings']
            overall_roi = ((total_winnings - total_stake) / total_stake * 100) if total_stake > 0 else 0
            
            table_data.append({
                'Season': result['target_season'],
                f'Top {top_n} Teams (FOR)': ', '.join(result['top_teams']),
                'FOR Bets': for_metrics['total_bets'],
                'FOR Win Rate (%)': f"{for_metrics['win_rate']:.1f}",
                'FOR ROI (%)': f"{for_metrics['roi']:+.1f}",
                f'Bottom {top_n} Teams (AGAINST)': ', '.join(result['bottom_teams']),
                'AGAINST Bets': against_metrics['total_bets'],
                'AGAINST Win Rate (%)': f"{against_metrics['win_rate']:.1f}",
                'AGAINST ROI (%)': f"{against_metrics['roi']:+.1f}",
                'Total Bets': total_bets,
                'Overall Win Rate (%)': f"{overall_win_rate:.1f}",
                'Overall ROI (%)': f"{overall_roi:+.1f}"
            })
        
        return pd.DataFrame(table_data)
    
    @staticmethod
    def print_summary_statistics(backtest_result: Dict) -> None:
        """
        Print summary statistics for a backtest result.
        
        Args:
            backtest_result (Dict): Backtest result
        """
        if 'error' in backtest_result:
            print(f"Error: {backtest_result['error']}")
            return
        
        print(f"\n{'='*100}")
        print("SUMMARY STATISTICS")
        print(f"{'='*100}")
        
        overall = backtest_result['overall']
        for_bets = backtest_result['for_bets']
        against_bets = backtest_result['against_bets']
        
        print(f"FOR BETS (Top Teams):")
        print(f"  Total Bets: {for_bets['total_bets']:,}")
        print(f"  Win Rate: {for_bets['win_rate']:.1f}%")
        print(f"  ROI: {for_bets['roi']:+.1f}%")
        print(f"  Profit/Loss: {for_bets['profit_loss']:+.0f} units")
        
        print(f"\nAGAINST BETS (Bottom Teams):")
        print(f"  Total Bets: {against_bets['total_bets']:,}")
        print(f"  Win Rate: {against_bets['win_rate']:.1f}%")
        print(f"  ROI: {against_bets['roi']:+.1f}%")
        print(f"  Profit/Loss: {against_bets['profit_loss']:+.0f} units")
        
        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Total Bets: {overall['total_bets']:,}")
        print(f"  Win Rate: {overall['win_rate']:.1f}%")
        print(f"  ROI: {overall['roi']:+.1f}%")
        print(f"  Profit/Loss: {overall['profit_loss']:+.0f} units")
        
        # Calculate profitable seasons
        season_results = backtest_result['season_results']
        profitable_seasons = sum(1 for result in season_results if result['roi'] > 0)
        
        print(f"\nPROFITABILITY:")
        print(f"  Profitable seasons: {profitable_seasons}/{len(season_results)} ({profitable_seasons/len(season_results)*100:.1f}%)")
    
    @staticmethod
    def print_yearly_breakdown(season_results: List[Dict]) -> None:
        """
        Print detailed yearly breakdown.
        
        Args:
            season_results (List[Dict]): List of season results
        """
        print(f"\n{'='*150}")
        print("YEAR-BY-YEAR BREAKDOWN")
        print(f"{'='*150}")
        
        df = ResultsAnalyzer.create_yearly_table(season_results)
        print(df.to_string(index=False))
    
    @staticmethod
    def analyze_team_performance(season_results: List[Dict]) -> pd.DataFrame:
        """
        Analyze performance by individual teams.
        
        Args:
            season_results (List[Dict]): List of season results
            
        Returns:
            pd.DataFrame: Team performance analysis
        """
        team_stats = {}
        
        for result in season_results:
            for bet in result['bet_details']:
                team = bet['bet_team']
                bet_type = bet['bet_type']
                
                if team not in team_stats:
                    team_stats[team] = {
                        'for_bets': 0, 'for_wins': 0, 'for_stake': 0, 'for_winnings': 0,
                        'against_bets': 0, 'against_wins': 0, 'against_stake': 0, 'against_winnings': 0
                    }
                
                if bet_type == 'FOR':
                    team_stats[team]['for_bets'] += 1
                    if bet['bet_wins']:
                        team_stats[team]['for_wins'] += 1
                    team_stats[team]['for_stake'] += bet['stake']
                    team_stats[team]['for_winnings'] += bet['winnings']
                else:
                    team_stats[team]['against_bets'] += 1
                    if bet['bet_wins']:
                        team_stats[team]['against_wins'] += 1
                    team_stats[team]['against_stake'] += bet['stake']
                    team_stats[team]['against_winnings'] += bet['winnings']
        
        # Calculate metrics for each team
        team_performance = []
        for team, stats in team_stats.items():
            for_win_rate = (stats['for_wins'] / stats['for_bets'] * 100) if stats['for_bets'] > 0 else 0
            for_roi = ((stats['for_winnings'] - stats['for_stake']) / stats['for_stake'] * 100) if stats['for_stake'] > 0 else 0
            
            against_win_rate = (stats['against_wins'] / stats['against_bets'] * 100) if stats['against_bets'] > 0 else 0
            against_roi = ((stats['against_winnings'] - stats['against_stake']) / stats['against_stake'] * 100) if stats['against_stake'] > 0 else 0
            
            team_performance.append({
                'Team': team,
                'FOR Bets': stats['for_bets'],
                'FOR Win Rate (%)': round(for_win_rate, 1),
                'FOR ROI (%)': round(for_roi, 1),
                'AGAINST Bets': stats['against_bets'],
                'AGAINST Win Rate (%)': round(against_win_rate, 1),
                'AGAINST ROI (%)': round(against_roi, 1)
            })
        
        # Sort by total bets
        team_performance.sort(key=lambda x: x['FOR Bets'] + x['AGAINST Bets'], reverse=True)
        
        return pd.DataFrame(team_performance)
