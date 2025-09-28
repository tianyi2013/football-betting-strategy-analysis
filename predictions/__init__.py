"""
Predictions Module

This module contains all prediction-related functionality including:
- Betting advisor logic
- Next round predictions
- Prediction utilities
"""

from .betting_advisor import BettingAdvisor, get_betting_advice
from .next_round_predictor import NextRoundPredictor
from .prediction_runner import run_predictions

__all__ = [
    'BettingAdvisor',
    'get_betting_advice', 
    'NextRoundPredictor',
    'run_predictions'
]
