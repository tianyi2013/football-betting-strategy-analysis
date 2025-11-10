"""
Performance metrics calculation and analysis
"""

from typing import Dict, List

import pandas as pd


class PerformanceMetrics:
    """
    Calculate and analyze betting performance metrics.
    """
    
    @staticmethod
    def calculate_metrics(bet_details: List[Dict]) -> Dict:
        """
        Calculate performance metrics from bet details.
        
        Args:
            bet_details (List[Dict]): List of bet details
            
        Returns:
            Dict: Performance metrics
        """
        if not bet_details:
            return {
                'total_bets': 0,
                'winning_bets': 0,
                'win_rate': 0.0,
                'total_stake': 0,
                'total_winnings': 0,
                'profit_loss': 0.0,
                'roi': 0.0
            }
        
        total_bets = len(bet_details)
        winning_bets = sum(1 for bet in bet_details if bet['bet_wins'])
        total_stake = sum(bet['stake'] for bet in bet_details)
        total_winnings = sum(bet['winnings'] for bet in bet_details)
        
        win_rate = (winning_bets / total_bets * 100) if total_bets > 0 else 0
        profit_loss = total_winnings - total_stake
        roi = (profit_loss / total_stake * 100) if total_stake > 0 else 0
        
        return {
            'total_bets': total_bets,
            'winning_bets': winning_bets,
            'win_rate': round(win_rate, 2),
            'total_stake': total_stake,
            'total_winnings': total_winnings,
            'profit_loss': round(profit_loss, 2),
            'roi': round(roi, 2)
        }
    
    @staticmethod
    def calculate_separate_metrics(bet_details: List[Dict]) -> Dict:
        """
        Calculate separate metrics for FOR and AGAINST bets.
        
        Args:
            bet_details (List[Dict]): List of bet details
            
        Returns:
            Dict: Separate metrics for FOR and AGAINST bets
        """
        for_bets = [bet for bet in bet_details if bet['bet_type'] == 'FOR']
        against_bets = [bet for bet in bet_details if bet['bet_type'] == 'AGAINST']
        
        for_metrics = PerformanceMetrics.calculate_metrics(for_bets)
        against_metrics = PerformanceMetrics.calculate_metrics(against_bets)
        
        return {
            'for_bets': for_metrics,
            'against_bets': against_metrics
        }
    
    @staticmethod
    def create_summary_table(season_results: List[Dict]) -> pd.DataFrame:
        """
        Create a summary table from season results.
        
        Args:
            season_results (List[Dict]): List of season results
            
        Returns:
            pd.DataFrame: Summary table
        """
        table_data = []
        
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
                'Top 3 Teams (FOR)': ', '.join(result['top_teams']),
                'FOR Bets': for_metrics['total_bets'],
                'FOR Win Rate (%)': f"{for_metrics['win_rate']:.1f}",
                'FOR ROI (%)': f"{for_metrics['roi']:+.1f}",
                'Bottom 3 Teams (AGAINST)': ', '.join(result['bottom_teams']),
                'AGAINST Bets': against_metrics['total_bets'],
                'AGAINST Win Rate (%)': f"{against_metrics['win_rate']:.1f}",
                'AGAINST ROI (%)': f"{against_metrics['roi']:+.1f}",
                'Total Bets': total_bets,
                'Overall Win Rate (%)': f"{overall_win_rate:.1f}",
                'Overall ROI (%)': f"{overall_roi:+.1f}"
            })
        
        return pd.DataFrame(table_data)
    
    @staticmethod
    def calculate_overall_statistics(season_results: List[Dict]) -> Dict:
        """
        Calculate overall statistics across all seasons.
        
        Args:
            season_results (List[Dict]): List of season results
            
        Returns:
            Dict: Overall statistics
        """
        all_for_bets = []
        all_against_bets = []
        
        for result in season_results:
            for bet in result['bet_details']:
                if bet['bet_type'] == 'FOR':
                    all_for_bets.append(bet)
                else:
                    all_against_bets.append(bet)
        
        for_metrics = PerformanceMetrics.calculate_metrics(all_for_bets)
        against_metrics = PerformanceMetrics.calculate_metrics(all_against_bets)
        
        # Overall metrics
        total_bets = for_metrics['total_bets'] + against_metrics['total_bets']
        total_wins = for_metrics['winning_bets'] + against_metrics['winning_bets']
        overall_win_rate = (total_wins / total_bets * 100) if total_bets > 0 else 0
        total_stake = for_metrics['total_stake'] + against_metrics['total_stake']
        total_winnings = for_metrics['total_winnings'] + against_metrics['total_winnings']
        overall_roi = ((total_winnings - total_stake) / total_stake * 100) if total_stake > 0 else 0
        
        return {
            'for_bets': for_metrics,
            'against_bets': against_metrics,
            'overall': {
                'total_bets': total_bets,
                'winning_bets': total_wins,
                'win_rate': round(overall_win_rate, 2),
                'total_stake': total_stake,
                'total_winnings': total_winnings,
                'profit_loss': round(total_winnings - total_stake, 2),
                'roi': round(overall_roi, 2)
            }
        }
