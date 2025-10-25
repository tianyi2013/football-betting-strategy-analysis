#!/usr/bin/env python3
"""
Simple Football Betting Logger Web Interface
Real-time predictions from your betting algorithm with robust database storage
"""

import json
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime

from flask import Flask, jsonify, request, make_response

# Add the parent directory to the path to import prediction modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictions.next_round_predictor import NextRoundPredictor
from ui.data_storage.storage_adapter import get_storage_adapter, SQLiteStorageAdapter

app = Flask(__name__)

# Global flag to prevent multiple browser openings
_browser_opened = False

# ...existing code...

# League configuration
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAGUES = {
    'premier_league': {
        'display_name': 'Premier League',
        'data_dir': os.path.join(_base_dir, 'data', 'premier_league')
    },
    'bundesliga_1': {
        'display_name': 'Bundesliga',
        'data_dir': os.path.join(_base_dir, 'data', 'bundesliga_1')
    },
    'laliga_1': {
        'display_name': 'La Liga',
        'data_dir': os.path.join(_base_dir, 'data', 'laliga_1')
    },
    'le_championnat': {
        'display_name': 'Ligue 1',
        'data_dir': os.path.join(_base_dir, 'data', 'le_championnat')
    },
    'serie_a': {
        'display_name': 'Serie A',
        'data_dir': os.path.join(_base_dir, 'data', 'serie_a')
    }
}


def get_real_opportunities():
    """Get real betting opportunities from prediction system"""
    opportunities = []

    print(f"Getting opportunities for {len(LEAGUES)} leagues...")

    for league_key, league_info in LEAGUES.items():
        try:
            print(f"Processing {league_info['display_name']}...")
            # Initialize predictor for this league
            predictor = NextRoundPredictor(league_info['data_dir'])

            # Get predictions for current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            print(f"Getting predictions for {current_date}...")
            print(f"Data directory: {league_info['data_dir']}")
            result = predictor.get_next_round_predictions(current_date)

            print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")

            if 'error' not in result and result.get('predictions'):
                print(f"Found {len(result['predictions'])} predictions for {league_info['display_name']}")
                for pred in result['predictions']:
                    recommendation = pred.get('recommendation', {})
                    if recommendation.get('bet_team'):
                        # Determine primary strategy based on individual strategies
                        individual_strategies = pred.get('individual_strategies', {})
                        primary_strategy = 'weighted'
                        strategy_priority = 3  # Default priority (lower = higher priority)

                        # Check which strategies are supporting this bet
                        supporting = recommendation.get('supporting_strategies', [])
                        if any('momentum' in s.lower() for s in supporting):
                            primary_strategy = 'momentum'
                            strategy_priority = 1
                        elif any('form' in s.lower() for s in supporting):
                            primary_strategy = 'form'
                            strategy_priority = 2

                        # Get actual game date from the prediction data
                        game_date = pred.get('match_date', result.get('round_date', 'Unknown'))

                        opportunities.append({
                            'league': league_info['display_name'],
                            'game': pred.get('game', 'Unknown vs Unknown'),
                            'bet_team': recommendation['bet_team'],
                            'bet_type': 'WIN',
                            'strategy': primary_strategy,
                            'confidence': recommendation.get('confidence', 0.5),
                            'reason': recommendation.get('reason', 'No reason provided'),
                            'round_number': result.get('next_round', 'Unknown'),
                            'match_date': game_date,  # Use actual game date instead of round start date
                            'supporting_strategies': recommendation.get('supporting_strategies', []),
                            'individual_strategies': individual_strategies,
                            'strategy_priority': strategy_priority
                        })
            else:
                print(f"No predictions or error for {league_info['display_name']}: {result.get('error', 'No predictions')}")
        except Exception as e:
            print(f"Error getting predictions for {league_info['display_name']}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"Total opportunities found: {len(opportunities)}")

    # Sort opportunities by date first (near future first), then by strategy priority and confidence
    def sort_key(opp):
        # Parse the match date for sorting
        match_date = opp.get('match_date', 'Unknown')
        if match_date == 'Unknown':
            return (999, 999, 0)  # Put unknown dates last

        try:
            # Handle DD/MM/YYYY format
            if '/' in match_date:
                parts = match_date.split('/')
                if len(parts) == 3:
                    # Assume DD/MM/YYYY format
                    date_obj = datetime.strptime(f"{parts[2]}-{parts[1]}-{parts[0]}", '%Y-%m-%d')
                else:
                    date_obj = datetime.strptime(match_date, '%Y-%m-%d')
            else:
                # Handle YYYY-MM-DD format
                date_obj = datetime.strptime(match_date, '%Y-%m-%d')

            # Return (days_from_now, strategy_priority, -confidence)
            days_from_now = (date_obj - datetime.now()).days
            return (days_from_now, opp.get('strategy_priority', 3), -opp.get('confidence', 0))
        except:
            return (999, 999, 0)  # Put invalid dates last

    opportunities.sort(key=sort_key)

    return opportunities


# Initialize storage adapter (SQLite database)
# Use absolute path to ensure we find the database regardless of working directory
import os
_db_path = os.path.join(os.path.dirname(__file__), 'data_storage', 'betting_data.db')
storage = get_storage_adapter(storage_type='sqlite', db_path=_db_path)

# Legacy JSON file path for potential migration
BETS_FILE = 'bets.json'

# Convenience function to get all bets
def get_all_bets():
    """Get all bets from database"""
    try:
        bets = storage.get_all_bets()
        return bets if bets else []
    except Exception as e:
        print(f"Error loading bets: {e}")
        return []


def save_bets_to_db(bets_data):
    """
    Save/update bets in database.
    This is called when the client sends updated bets list.
    """
    try:
        # For each bet, update if exists or create new
        for bet in bets_data:
            if 'id' in bet and isinstance(bet['id'], int):
                # Update existing
                storage.update_bet(bet['id'], bet)
            else:
                # Add new
                storage.add_bet(bet)
    except Exception as e:
        print(f"Error saving bets: {e}")



@app.route('/')
def index():
    """Serve the main HTML page"""
    # Add cache-busting headers to prevent browser caching
    response = make_response(HTML_TEMPLATE)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Football Betting Logger</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .main-content {
            padding: 30px;
        }

        .tabs {
            display: flex;
            margin-bottom: 30px;
            border-bottom: 2px solid #ecf0f1;
        }

        .tab {
            padding: 15px 30px;
            background: #f8f9fa;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            color: #6c757d;
            transition: all 0.3s ease;
            border-radius: 10px 10px 0 0;
            margin-right: 5px;
        }

        .tab.active {
            background: #3498db;
            color: white;
        }

        .tab:hover {
            background: #2980b9;
            color: white;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .opportunities-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .opportunity-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }

        .opportunity-card:hover {
            border-color: #3498db;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.2);
        }

        .opportunity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }

        .league-badge {
            background: #3498db;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .confidence-badge {
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
        }

        .game-info {
            margin-bottom: 15px;
        }

        .game-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        .bet-details {
            color: #6c757d;
            font-size: 14px;
        }

        .bet-inputs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
        }

        .input-group label {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        .input-group input {
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }

        .input-group input:focus {
            outline: none;
            border-color: #3498db;
        }

        .bet-actions {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: #3498db;
            color: white;
        }

        .btn-primary:hover {
            background: #2980b9;
        }

        .btn-success {
            background: #27ae60;
            color: white;
        }

        .btn-success:hover {
            background: #229954;
        }

        .btn-danger {
            background: #e74c3c;
            color: white;
        }

        .btn-danger:hover {
            background: #c0392b;
        }

        .summary-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .summary-item {
            text-align: center;
        }

        .summary-value {
            font-size: 2em;
            font-weight: 700;
            color: #2c3e50;
        }

        .summary-label {
            color: #6c757d;
            font-size: 14px;
            margin-top: 5px;
        }

        .calculate-btn {
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }

        .calculate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(39, 174, 96, 0.3);
        }

        .clear-btn {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            margin-top: 20px;
        }

        .clear-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(231, 76, 60, 0.3);
        }

        .bets-list {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }

        .bet-item {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .bet-info {
            flex: 1;
        }

        .bet-amount {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
        }

        .bet-odds {
            color: #6c757d;
            font-size: 14px;
        }

        .bet-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-pending {
            background: #f39c12;
            color: white;
        }

        .status-won {
            background: #27ae60;
            color: white;
        }

        .status-lost {
            background: #e74c3c;
            color: white;
        }

        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }

        .error {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .bet-breakdown {
            margin-top: 30px;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }

        .breakdown-tabs {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }

        .breakdown-tab {
            padding: 10px 20px;
            background: #f8f9fa;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #6c757d;
            transition: all 0.3s ease;
            border-radius: 8px 8px 0 0;
            margin-right: 5px;
        }

        .breakdown-tab.active {
            background: #3498db;
            color: white;
        }

        .breakdown-tab:hover {
            background: #2980b9;
            color: white;
        }

        .bet-breakdown-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .breakdown-bet-item {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 15px;
            align-items: center;
        }

        .breakdown-bet-info {
            flex: 1;
        }

        .breakdown-bet-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        .breakdown-bet-details {
            color: #6c757d;
            font-size: 14px;
            margin-bottom: 5px;
        }

        .breakdown-bet-meta {
            color: #95a5a6;
            font-size: 12px;
        }

        .breakdown-bet-amounts {
            text-align: right;
        }

        .strategy-details {
            transition: all 0.3s ease;
        }

        .strategy-toggle-btn:hover {
            background: #e9ecef !important;
            border-color: #adb5bd !important;
        }

        .strategy-badge {
            transition: all 0.3s ease;
        }

        /* Round Analytics Styles */
        .round-analytics-section {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .round-analytics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .round-card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }

        .round-card:hover {
            border-color: #3498db;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.2);
        }

        .round-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }

        .round-header h4 {
            margin: 0;
            color: #2c3e50;
            font-size: 18px;
        }

        .round-status {
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
        }

        .round-status.active {
            background: #fff3cd;
            color: #856404;
        }

        .round-status.completed {
            background: #d4edda;
            color: #155724;
        }

        .round-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }

        .stat-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
        }

        .stat-label {
            font-weight: 600;
            color: #6c757d;
            font-size: 14px;
        }

        .stat-value {
            font-weight: 700;
            font-size: 16px;
            color: #2c3e50;
        }

        .stat-value.profit-positive {
            color: #27ae60;
        }

        .stat-value.profit-negative {
            color: #e74c3c;
        }

        /* Weekend Info Styles */
        .weekend-info {
            margin-bottom: 15px;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }

        .weekend-leagues {
            font-size: 13px;
            color: #6c757d;
            font-style: italic;
            background: #f8f9fa;
            padding: 5px 10px;
            border-radius: 5px;
            display: inline-block;
        }
        
        /* Date Filter Styles */
        .date-filter-section {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        }
        
        .date-filter-section label {
            font-weight: 600;
            color: #495057;
            margin-right: 10px;
        }
        
        #date-filter {
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background: white;
            font-size: 14px;
            margin-right: 10px;
            min-width: 150px;
        }
        
        .clear-filter-btn {
            background: #6c757d;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .clear-filter-btn:hover {
            background: #5a6268;
        }

        /* Performance Summary Styles */
        .performance-summary {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }

        .performance-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .performance-card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s ease;
        }

        .performance-card:hover {
            border-color: #3498db;
            box-shadow: 0 5px 15px rgba(52, 152, 219, 0.2);
        }

        .performance-card h4 {
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 18px;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }

        .performance-stats {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .perf-stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #f8f9fa;
        }

        .perf-stat:last-child {
            border-bottom: none;
        }

        .perf-label {
            font-weight: 600;
            color: #6c757d;
            font-size: 14px;
        }

        .perf-value {
            font-weight: 700;
            font-size: 16px;
            color: #2c3e50;
        }

        .perf-value.profit-positive {
            color: #27ae60;
        }

        .perf-value.profit-negative {
            color: #e74c3c;
        }

        .breakdown-stake {
            font-size: 16px;
            font-weight: 600;
            color: #2c3e50;
        }

        .breakdown-odds {
            color: #6c757d;
            font-size: 14px;
        }

        .breakdown-profit {
            font-size: 18px;
            font-weight: 700;
            text-align: right;
        }

        .profit-positive {
            color: #27ae60;
        }

        .profit-negative {
            color: #e74c3c;
        }

        .profit-pending {
            color: #f39c12;
        }

        .breakdown-status {
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 600;
            text-align: center;
        }

        .status-won {
            background: #d4edda;
            color: #155724;
        }

        .status-lost {
            background: #f8d7da;
            color: #721c24;
        }

        .status-pending {
            background: #fff3cd;
            color: #856404;
        }

        @media (max-width: 768px) {
            .opportunities-grid {
                grid-template-columns: 1fr;
            }
            
            .bet-inputs {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-wrap: wrap;
            }
            
            .breakdown-bet-item {
                grid-template-columns: 1fr;
                text-align: center;
            }
            
            .breakdown-bet-amounts {
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚽ Football Betting Logger</h1>
            <p>Track your betting opportunities and calculate P&L</p>
        </div>

        <div class="main-content">
            <div class="tabs">
                <button class="tab active" onclick="showTab('opportunities')">Opportunities</button>
                <button class="tab" onclick="showTab('bets')">My Bets</button>
                <button class="tab" onclick="showTab('analytics')">Analytics</button>
            </div>

            <!-- Opportunities Tab -->
            <div id="opportunities" class="tab-content active">
                <h2>Available Betting Opportunities</h2>
                
                <!-- Date Filter -->
                <div class="date-filter-section">
                    <label for="date-filter">Filter by Date:</label>
                    <select id="date-filter" onchange="filterOpportunitiesByDate()">
                        <option value="all">All Dates</option>
                        <!-- Date options will be populated dynamically -->
                    </select>
                    <button onclick="clearDateFilter()" class="clear-filter-btn">Clear Filter</button>
                </div>
                
                <div id="opportunities-grid" class="opportunities-grid">
                    <!-- Opportunities will be populated here -->
                </div>
            </div>

            <!-- My Bets Tab -->
            <div id="bets" class="tab-content">
                <h2>My Active Bets</h2>
                <div id="bets-list" class="bets-list">
                    <p>No active bets yet. Add some opportunities from the Opportunities tab!</p>
                </div>
            </div>

            <!-- Analytics Tab -->
            <div id="analytics" class="tab-content">
                <h2>Betting Analytics</h2>
                <!-- Settled Bets Section -->
                <div class="summary-card" style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">📊 Settled Bets</h3>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-value" id="settled-bets">0</div>
                            <div class="summary-label">Settled Bets</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" id="win-rate">0%</div>
                            <div class="summary-label">Win Rate</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" id="settled-stake">£0</div>
                            <div class="summary-label">Settled Stake</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" id="total-profit">£0</div>
                            <div class="summary-label">Total Profit</div>
                        </div>
                    </div>
                </div>
                
                <!-- Pending Bets Section -->
                <div class="summary-card">
                    <h3 style="margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;">⏳ Pending Bets</h3>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-value" id="pending-bets">0</div>
                            <div class="summary-label">Pending Bets</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" id="pending-stake">£0</div>
                            <div class="summary-label">Pending Stake</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" id="potential-profit">£0</div>
                            <div class="summary-label">Potential Profit</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" id="total-bets">0</div>
                            <div class="summary-label">Total Bets</div>
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                    <button class="calculate-btn" onclick="calculatePnL()" style="flex: 1;">Calculate P&L</button>
                    <button class="clear-btn" onclick="clearAllHistory()" style="flex: 1; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);">Clear All History</button>
                </div>
                
                <!-- Weekend Analytics Section -->
                <div class="round-analytics-section" style="margin-top: 30px;">
                    <h3>Weekend-by-Weekend Analytics</h3>
                    <div id="round-analytics">
                        <!-- Weekend analytics will be populated here -->
                    </div>
                </div>
                
                <!-- Overall Performance Summary -->
                <div class="performance-summary" style="margin-top: 30px; background: #f8f9fa; border-radius: 10px; padding: 20px;">
                    <h3>Overall Performance Summary</h3>
                    <div id="performance-summary-content">
                        <!-- Performance summary will be populated here -->
                    </div>
                </div>
                
                <!-- Bet Breakdown Section -->
                <div class="bet-breakdown">
                    <h3>Bet Breakdown</h3>
                    <div class="breakdown-tabs">
                        <button class="breakdown-tab active" onclick="showBreakdown('all')">All Bets</button>
                        <button class="breakdown-tab" onclick="showBreakdown('active')">Active</button>
                        <button class="breakdown-tab" onclick="showBreakdown('completed')">Completed</button>
                    </div>
                    <div id="bet-breakdown-list" class="bet-breakdown-list">
                        <!-- Bet details will be populated here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let opportunities = [];
        let activeBets = [];
        let completedBets = [];
        let currentDateFilter = 'all';  // Track current filter state

        // Date filtering functions
        function populateDateFilter() {
            const dateFilter = document.getElementById('date-filter');
            const uniqueDates = [...new Set(opportunities.map(opp => opp.match_date))].sort();
            
            // Clear existing options except "All Dates"
            dateFilter.innerHTML = '<option value="all">All Dates</option>';
            
            // Add date options
            uniqueDates.forEach(date => {
                const option = document.createElement('option');
                option.value = date;  // Keep the raw date value for filtering
                option.textContent = formatDateForDisplay(date);  // Display formatted date
                dateFilter.appendChild(option);
            });
        }
        
        function formatDateForDisplay(dateStr) {
            if (!dateStr || dateStr === 'Unknown') return 'Unknown Date';
            
            try {
                // Handle DD/MM/YYYY format
                if (dateStr.includes('/')) {
                    const parts = dateStr.split('/');
                    if (parts.length === 3) {
                        const day = parts[0];
                        const month = parts[1];
                        const year = parts[2];
                        const date = new Date(year, month - 1, day);
                        return date.toLocaleDateString('en-US', { 
                            weekday: 'short', 
                            year: 'numeric', 
                            month: 'short', 
                            day: 'numeric' 
                        });
                    }
                }
                
                // Handle YYYY-MM-DD format
                const date = new Date(dateStr);
                return date.toLocaleDateString('en-US', { 
                    weekday: 'short', 
                    year: 'numeric', 
                    month: 'short', 
                    day: 'numeric' 
                });
            } catch (e) {
                return dateStr;
            }
        }
        
        function filterOpportunitiesByDate() {
            const selectedDate = document.getElementById('date-filter').value;
            currentDateFilter = selectedDate;  // Save current filter state
            console.log('Selected date:', selectedDate);
            
            const filteredOpportunities = selectedDate === 'all' 
                ? opportunities 
                : opportunities.filter(opp => {
                    console.log('Comparing:', opp.match_date, '===', selectedDate, '?', opp.match_date === selectedDate);
                    return opp.match_date === selectedDate;
                });
            
            console.log('Filtered opportunities:', filteredOpportunities.length, 'out of', opportunities.length);
            displayOpportunities(filteredOpportunities);
        }
        
        function clearDateFilter() {
            document.getElementById('date-filter').value = 'all';
            currentDateFilter = 'all';  // Reset filter state
            displayOpportunities(opportunities);
        }

        // Initialize the app
        document.addEventListener('DOMContentLoaded', function() {
            loadOpportunities();
            loadBets().then(() => {
                updateAnalytics();
            });
        });

        // Tab switching
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Update displays based on tab
            if (tabName === 'bets') {
                updateBetsDisplay();
            } else if (tabName === 'analytics') {
                updateAnalytics();
            }
        }

        // Load betting opportunities
        async function loadOpportunities() {
            try {
                const response = await fetch('/api/opportunities');
                if (!response.ok) {
                    throw new Error('Failed to load opportunities');
                }
                opportunities = await response.json();
                populateDateFilter(); // Populate the date filter
                displayOpportunities();
            } catch (error) {
                console.error('Error loading opportunities:', error);
                showError('Failed to load betting opportunities. Please try again later.');
            }
        }

        // Display opportunities
        function displayOpportunities(opportunitiesToShow = null) {
            const grid = document.getElementById('opportunities-grid');
            const opportunitiesToDisplay = opportunitiesToShow || opportunities;
            
            grid.innerHTML = '';
            
            if (opportunitiesToDisplay.length === 0) {
                grid.innerHTML = '<p>No betting opportunities available for the selected date.</p>';
                return;
            }
            
            opportunitiesToDisplay.forEach((opp, displayIndex) => {
                // Find the actual index in the full opportunities array
                const actualIndex = opportunities.findIndex(o => 
                    o.game === opp.game && 
                    o.bet_team === opp.bet_team && 
                    o.league === opp.league
                );
                const card = createOpportunityCard(opp, actualIndex);
                grid.appendChild(card);
            });
        }

        // Check if opportunity already has a bet placed
        function hasBetOnOpportunity(opportunity) {
            const allBets = [...activeBets, ...completedBets];
            return allBets.some(bet => {
                // Support both old format (with opportunity nested) and new format (flat)
                const betGame = bet.opportunity?.game || bet.game;
                const betTeam = bet.opportunity?.bet_team || bet.bet_team;
                const betLeague = bet.opportunity?.league || bet.league;
                return betGame === opportunity.game && 
                       betTeam === opportunity.bet_team &&
                       betLeague === opportunity.league;
            });
        }

        // Create opportunity card
        function createOpportunityCard(opportunity, index) {
            const card = document.createElement('div');
            const hasExistingBet = hasBetOnOpportunity(opportunity);
            
            // Add visual indicator for existing bets
            if (hasExistingBet) {
                card.className = 'opportunity-card bet-placed';
                card.style.border = '2px solid #27ae60';
                card.style.backgroundColor = '#f8fff8';
            } else {
                card.className = 'opportunity-card';
            }
            
            // Format date if available
            const matchDate = opportunity.match_date || 'TBD';
            const roundNumber = opportunity.round_number || 'Unknown';
            
            // Create strategy details HTML
            const individualStrategies = opportunity.individual_strategies || {};
            const strategyDetails = createStrategyDetailsHTML(individualStrategies);
            
            card.innerHTML = `
                <div class="opportunity-header">
                    <span class="league-badge">${opportunity.league}</span>
                    <span class="confidence-badge">${Math.round(opportunity.confidence * 100)}%</span>
                    <span class="strategy-badge" style="background: ${getStrategyColor(opportunity.strategy)}; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: 600; margin-left: 10px;">
                        ${opportunity.strategy.toUpperCase()}
                    </span>
                    ${hasExistingBet ? '<span class="bet-placed-badge" style="background: #27ae60; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: 600; margin-left: 10px;">✓ BET PLACED</span>' : ''}
                </div>
                <div class="game-info">
                    <div class="game-title">${opportunity.game}</div>
                    <div class="bet-details">
                        <strong>${opportunity.bet_team}</strong> - ${opportunity.bet_type} (${opportunity.strategy})
                    </div>
                    <div class="match-meta" style="margin-top: 8px; font-size: 12px; color: #6c757d;">
                        Round ${roundNumber} • ${matchDate}
                    </div>
                    <div class="bet-reason" style="margin-top: 8px; font-size: 13px; color: #495057; font-style: italic;">
                        ${opportunity.reason}
                    </div>
                </div>
                
                <!-- Collapsible Strategy Details -->
                <div class="strategy-details-section" style="margin-top: 15px;">
                    <button class="strategy-toggle-btn" onclick="toggleStrategyDetails(${index})" style="
                        background: #f8f9fa; 
                        border: 1px solid #dee2e6; 
                        padding: 8px 15px; 
                        border-radius: 5px; 
                        cursor: pointer; 
                        width: 100%; 
                        font-size: 14px;
                        font-weight: 600;
                        color: #495057;
                    ">
                        Strategy Analysis ▼
                    </button>
                    <div id="strategy-details-${index}" class="strategy-details" style="display: none; margin-top: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; border: 1px solid #dee2e6;">
                        ${strategyDetails}
                    </div>
                </div>
                
                ${hasExistingBet ? 
                    '<div style="text-align: center; padding: 20px; background: #f8fff8; border: 1px solid #27ae60; border-radius: 5px; color: #27ae60; font-weight: 600;">✓ You have already placed a bet on this opportunity</div>' :
                    `<div class="bet-inputs">
                        <div class="input-group">
                            <label>Odds</label>
                            <input type="text" id="odds-${index}" placeholder="e.g., 2.5 or 8/11" step="0.1">
                        </div>
                        <div class="input-group">
                            <label>Stake (£)</label>
                            <input type="number" id="stake-${index}" placeholder="e.g., 50" step="0.01" min="0.01">
                        </div>
                    </div>
                    <div class="bet-actions">
                        <button class="btn btn-primary" onclick="addBet(${index})">Add Bet</button>
                        <button class="btn btn-success" onclick="addBetAndMarkWon(${index})">Add & Mark Won</button>
                        <button class="btn btn-danger" onclick="addBetAndMarkLost(${index})">Add & Mark Lost</button>
                    </div>`
                }
            `;
            return card;
        }
        
        // Helper function to create strategy details HTML
        function createStrategyDetailsHTML(individualStrategies) {
            let html = '<div style="font-size: 13px;">';
            
            // Momentum Strategy
            const momentum = individualStrategies.momentum || {};
            html += `<div style="margin-bottom: 10px;">
                <strong>Momentum:</strong> ${momentum.bet_team || 'None'} (Confidence: ${Math.round((momentum.confidence || 0) * 100)}%)<br>
                <span style="color: #6c757d; font-size: 12px;">${momentum.reason || 'No reason provided'}</span>
            </div>`;
            
            // Form Strategy
            const form = individualStrategies.form || {};
            html += `<div style="margin-bottom: 10px;">
                <strong>Form:</strong> ${form.bet_team || 'None'} (Confidence: ${Math.round((form.confidence || 0) * 100)}%)<br>
                <span style="color: #6c757d; font-size: 12px;">${form.reason || 'No reason provided'}</span>
            </div>`;
            
            // Top-Bottom Strategy
            const topBottom = individualStrategies.top_bottom || {};
            html += `<div style="margin-bottom: 10px;">
                <strong>Top-Bottom:</strong> ${topBottom.bet_team || 'None'} (Confidence: ${Math.round((topBottom.confidence || 0) * 100)}%)<br>
                <span style="color: #6c757d; font-size: 12px;">${topBottom.reason || 'No reason provided'}</span>
            </div>`;
            
            // Home-Away Strategy
            const homeAway = individualStrategies.home_away || {};
            html += `<div style="margin-bottom: 10px;">
                <strong>Home-Away:</strong> ${homeAway.bet_team || 'None'} (Confidence: ${Math.round((homeAway.confidence || 0) * 100)}%)<br>
                <span style="color: #6c757d; font-size: 12px;">${homeAway.reason || 'No reason provided'}</span>
            </div>`;
            
            html += '</div>';
            return html;
        }
        
        // Helper function to get strategy color
        function getStrategyColor(strategy) {
            const colors = {
                'momentum': '#e74c3c',
                'form': '#f39c12', 
                'top_bottom': '#9b59b6',
                'home_away': '#3498db',
                'weighted': '#2ecc71'
            };
            return colors[strategy] || '#6c757d';
        }
        
        // Toggle strategy details
        function toggleStrategyDetails(index) {
            const details = document.getElementById(`strategy-details-${index}`);
            const button = details.previousElementSibling;
            
            if (details.style.display === 'none') {
                details.style.display = 'block';
                button.innerHTML = 'Strategy Analysis ▲';
            } else {
                details.style.display = 'none';
                button.innerHTML = 'Strategy Analysis ▼';
            }
        }

        // Convert fractional odds to decimal odds
        function convertFractionalOdds(fractionalOdds) {
            if (typeof fractionalOdds === 'number') {
                return Math.round(fractionalOdds * 1000) / 1000; // Round to 3 decimal places
            }
            
            const oddsStr = fractionalOdds.toString().trim();
            
            // Check if it's fractional format (e.g., "8/11", "2/1")
            if (oddsStr.includes('/')) {
                const parts = oddsStr.split('/');
                if (parts.length === 2) {
                    const numerator = parseFloat(parts[0]);
                    const denominator = parseFloat(parts[1]);
                    
                    if (!isNaN(numerator) && !isNaN(denominator) && denominator > 0) {
                        const decimalOdds = (numerator / denominator) + 1;
                        return Math.round(decimalOdds * 1000) / 1000; // Round to 3 decimal places
                    }
                }
            }
            
            // Try to parse as decimal
            const decimal = parseFloat(oddsStr);
            return isNaN(decimal) ? null : Math.round(decimal * 1000) / 1000; // Round to 3 decimal places
        }

        // Add bet functions
        function addBet(index) {
            const opportunity = opportunities[index];
            const oddsInput = document.getElementById(`odds-${index}`).value.trim();
            const stake = parseFloat(document.getElementById(`stake-${index}`).value);
            
            if (!oddsInput || !stake) {
                alert('Please enter both odds and stake amount.');
                return;
            }
            
            const odds = convertFractionalOdds(oddsInput);
            if (!odds || odds < 1.01) {
                alert('Please enter valid odds (e.g., 2.5 or 8/11).');
                return;
            }
            
            const bet = {
                id: Date.now(),
                opportunity: opportunity,
                odds: odds,
                stake: stake,
                status: 'pending',
                date: new Date().toISOString(),
                placement_date: new Date().toISOString(),
                match_date: opportunity.match_date
            };
            
            activeBets.push(bet);
            saveBets();
            updateBetsDisplay();
            updateAnalytics();
            
            // Clear inputs
            document.getElementById(`odds-${index}`).value = '';
            document.getElementById(`stake-${index}`).value = '';
            
            // Refresh opportunities display with current filter
            if (currentDateFilter === 'all') {
                displayOpportunities(opportunities);
            } else {
                const filteredOpportunities = opportunities.filter(opp => opp.match_date === currentDateFilter);
                displayOpportunities(filteredOpportunities);
            }
            
            alert('Bet added successfully!');
        }

        function addBetAndMarkWon(index) {
            const opportunity = opportunities[index];
            const oddsInput = document.getElementById(`odds-${index}`).value.trim();
            const stake = parseFloat(document.getElementById(`stake-${index}`).value);
            
            if (!oddsInput || !stake) {
                alert('Please enter both odds and stake amount.');
                return;
            }
            
            const odds = convertFractionalOdds(oddsInput);
            if (!odds || odds < 1.01) {
                alert('Please enter valid odds (e.g., 2.5 or 8/11).');
                return;
            }
            
            const bet = {
                id: Date.now(),
                opportunity: opportunity,
                odds: odds,
                stake: stake,
                status: 'won',
                result: 'Won',
                profit: (stake * odds) - stake,
                date: new Date().toISOString(),
                placement_date: new Date().toISOString(),
                match_date: opportunity.match_date
            };
            
            completedBets.push(bet);
            saveBets();
            updateBetsDisplay();
            updateAnalytics();
            
            // Clear inputs
            document.getElementById(`odds-${index}`).value = '';
            document.getElementById(`stake-${index}`).value = '';
            
            // Refresh opportunities display with current filter
            if (currentDateFilter === 'all') {
                displayOpportunities(opportunities);
            } else {
                const filteredOpportunities = opportunities.filter(opp => opp.match_date === currentDateFilter);
                displayOpportunities(filteredOpportunities);
            }
            
            alert('Bet added and marked as won!');
        }

        function addBetAndMarkLost(index) {
            const opportunity = opportunities[index];
            const oddsInput = document.getElementById(`odds-${index}`).value.trim();
            const stake = parseFloat(document.getElementById(`stake-${index}`).value);
            
            if (!oddsInput || !stake) {
                alert('Please enter both odds and stake amount.');
                return;
            }
            
            const odds = convertFractionalOdds(oddsInput);
            if (!odds || odds < 1.01) {
                alert('Please enter valid odds (e.g., 2.5 or 8/11).');
                return;
            }
            
            const bet = {
                id: Date.now(),
                opportunity: opportunity,
                odds: odds,
                stake: stake,
                status: 'lost',
                result: 'Lost',
                profit: -stake,
                date: new Date().toISOString(),
                placement_date: new Date().toISOString(),
                match_date: opportunity.match_date
            };
            
            completedBets.push(bet);
            saveBets();
            updateBetsDisplay();
            updateAnalytics();
            
            // Clear inputs
            document.getElementById(`odds-${index}`).value = '';
            document.getElementById(`stake-${index}`).value = '';
            
            // Refresh opportunities display with current filter
            if (currentDateFilter === 'all') {
                displayOpportunities(opportunities);
            } else {
                const filteredOpportunities = opportunities.filter(opp => opp.match_date === currentDateFilter);
                displayOpportunities(filteredOpportunities);
            }
            
            alert('Bet added and marked as lost!');
        }

        // Load and save bets using file-based storage
        async function loadBets() {
            try {
                const response = await fetch('/api/bets');
                if (response.ok) {
                    const allBets = await response.json();
                    activeBets = allBets.filter(bet => bet.status === 'pending');
                    completedBets = allBets.filter(bet => bet.status === 'won' || bet.status === 'lost');
                }
            } catch (error) {
                console.error('Error loading bets:', error);
            }
        }

        async function saveBets() {
            try {
                const allBets = [...activeBets, ...completedBets];
                const response = await fetch('/api/bets', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(allBets)
                });
                if (!response.ok) {
                    console.error('Error saving bets');
                }
            } catch (error) {
                console.error('Error saving bets:', error);
            }
        }

        // Update bets display
        function updateBetsDisplay() {
            const container = document.getElementById('bets-list');
            
            if (activeBets.length === 0) {
                container.innerHTML = '<p>No active bets. Add some opportunities from the Opportunities tab!</p>';
                return;
            }
            
            container.innerHTML = '';
            
            activeBets.forEach(bet => {
                const betItem = document.createElement('div');
                betItem.className = 'bet-item';
                // Support both old format (with opportunity nested) and new format (flat)
                const game = bet.opportunity?.game || bet.game || 'Unknown';
                const betTeam = bet.opportunity?.bet_team || bet.bet_team || 'Unknown';
                betItem.innerHTML = `
                    <div class="bet-info">
                        <div class="bet-amount">£${bet.stake.toFixed(2)} @ ${bet.odds.toFixed(3)}</div>
                        <div class="bet-odds">${game} - ${betTeam}</div>
                    </div>
                    <div>
                        <span class="bet-status status-pending">Pending</span>
                        <button class="btn btn-success" onclick="markBetWon(${bet.id})">Won</button>
                        <button class="btn btn-danger" onclick="markBetLost(${bet.id})">Lost</button>
                        <button class="btn btn-danger" onclick="deleteBet(${bet.id})" style="background: #e74c3c; margin-left: 5px;">Delete</button>
                    </div>
                `;
                container.appendChild(betItem);
            });
        }

        // Mark bet as won/lost
        function markBetWon(betId) {
            const betIndex = activeBets.findIndex(bet => bet.id === betId);
            if (betIndex !== -1) {
                const bet = activeBets[betIndex];
                bet.status = 'won';
                bet.result = 'Won';
                bet.profit = (bet.stake * bet.odds) - bet.stake;
                completedBets.push(bet);
                activeBets.splice(betIndex, 1);
                saveBets();
                updateBetsDisplay();
                updateAnalytics();
            }
        }

        function markBetLost(betId) {
            const betIndex = activeBets.findIndex(bet => bet.id === betId);
            if (betIndex !== -1) {
                const bet = activeBets[betIndex];
                bet.status = 'lost';
                bet.result = 'Lost';
                bet.profit = -bet.stake;
                completedBets.push(bet);
                activeBets.splice(betIndex, 1);
                saveBets();
                updateBetsDisplay();
                updateAnalytics();
            }
        }

        // Delete bet
        function deleteBet(betId) {
            if (confirm('Are you sure you want to delete this bet?')) {
                const betIndex = activeBets.findIndex(bet => bet.id === betId);
                if (betIndex !== -1) {
                    activeBets.splice(betIndex, 1);
                    saveBets();
                    updateBetsDisplay();
                    updateAnalytics();
                    // Refresh opportunities display to remove bet placed indicator
                    displayOpportunities();
                    alert('Bet deleted successfully!');
                }
            }
        }

        // Update analytics
        function updateAnalytics() {
            console.log('updateAnalytics called');
            const allBets = [...activeBets, ...completedBets];
            console.log('All bets:', allBets);
            const totalBets = allBets.length;
            const completedBetsCount = completedBets.length;
            const wonBets = completedBets.filter(bet => bet.status === 'won').length;
            const winRate = completedBetsCount > 0 ? Math.round((wonBets / completedBetsCount) * 100) : 0;
            const totalStake = allBets.reduce((sum, bet) => sum + bet.stake, 0);
            const totalProfit = completedBets.reduce((sum, bet) => sum + bet.profit, 0);
            
            // Calculate pending bet stats
            const pendingBetsCount = activeBets.length;
            const pendingStake = activeBets.reduce((sum, bet) => sum + bet.stake, 0);
            const potentialProfit = activeBets.reduce((sum, bet) => sum + ((bet.stake * bet.odds) - bet.stake), 0);
            
            console.log('Analytics stats:', { 
                totalBets, completedBetsCount, wonBets, winRate, 
                totalStake, totalProfit, pendingBetsCount, pendingStake, potentialProfit 
            });
            
            // Update settled bets section
            document.getElementById('settled-bets').textContent = completedBetsCount;
            document.getElementById('win-rate').textContent = winRate + '%';
            document.getElementById('settled-stake').textContent = '£' + (totalStake - pendingStake).toFixed(2);
            document.getElementById('total-profit').textContent = '£' + totalProfit.toFixed(2);
            
            // Update pending bets section
            document.getElementById('pending-bets').textContent = pendingBetsCount;
            document.getElementById('pending-stake').textContent = '£' + pendingStake.toFixed(2);
            document.getElementById('potential-profit').textContent = '£' + potentialProfit.toFixed(2);
            document.getElementById('total-bets').textContent = totalBets;
            
            // Update weekend-based analytics
            updateRoundAnalytics(allBets);
            
            // Update breakdown display
            updateBetBreakdown();
        }
        
        // Update weekend-based analytics
        function updateRoundAnalytics(allBets) {
            console.log('updateRoundAnalytics called with bets:', allBets);
            const weekendStats = {};
            
            // Group bets by weekend using bet placement date
            allBets.forEach(bet => {
                // Use bet placement date instead of match date for weekend grouping
                const betDate = bet.placement_date || bet.date || 'Unknown';
                const weekend = getWeekendLabel(betDate);
                console.log('Bet placement date:', betDate, 'Weekend:', weekend);
                
                if (!weekendStats[weekend]) {
                    weekendStats[weekend] = {
                        totalBets: 0,
                        wonBets: 0,
                        totalStake: 0,
                        totalProfit: 0,
                        activeBets: 0,
                        completedBets: 0,
                        matchDate: betDate,
                        leagues: new Set()
                    };
                }
                
                weekendStats[weekend].totalBets++;
                weekendStats[weekend].totalStake += bet.stake;
                
                // Track leagues for this weekend (support both flat and nested structures)
                const league = bet.league || bet.opportunity?.league;
                if (league) {
                    weekendStats[weekend].leagues.add(league);
                }
                
                if (bet.status === 'won') {
                    weekendStats[weekend].wonBets++;
                    weekendStats[weekend].totalProfit += bet.profit || 0;
                    weekendStats[weekend].completedBets++;
                } else if (bet.status === 'lost') {
                    weekendStats[weekend].totalProfit += bet.profit || 0;
                    weekendStats[weekend].completedBets++;
                } else {
                    weekendStats[weekend].activeBets++;
                }
            });
            
            // Update weekend analytics display
            updateWeekendAnalyticsDisplay(weekendStats);
            
            // Update performance summary
            updatePerformanceSummary(weekendStats);
        }
        
        // Get weekend label from bet date
        function getWeekendLabel(betDate) {
            if (betDate === 'Unknown' || !betDate) {
                return 'Unknown Weekend';
            }
            
            try {
                // Handle different date formats
                let date;
                if (betDate.includes('/')) {
                    // Handle DD/MM/YYYY format
                    const parts = betDate.split('/');
                    if (parts.length === 3) {
                        // Assume DD/MM/YYYY format
                        date = new Date(parts[2], parts[1] - 1, parts[0]);
                    } else {
                        date = new Date(betDate);
                    }
                } else {
                    // Handle ISO format (YYYY-MM-DDTHH:mm:ss.sssZ)
                    date = new Date(betDate);
                }
                
                if (isNaN(date.getTime())) {
                    return 'Unknown Weekend';
                }
                
                // Get the weekend (Friday-Sunday) of this date
                const dayOfWeek = date.getDay();
                let weekendStart, weekendEnd;
                
                if (dayOfWeek === 0) { // Sunday
                    weekendStart = new Date(date);
                    weekendStart.setDate(date.getDate() - 2); // Friday
                    weekendEnd = new Date(date);
                } else if (dayOfWeek === 6) { // Saturday
                    weekendStart = new Date(date);
                    weekendStart.setDate(date.getDate() - 1); // Friday
                    weekendEnd = new Date(date);
                    weekendEnd.setDate(date.getDate() + 1); // Sunday
                } else if (dayOfWeek === 5) { // Friday
                    weekendStart = new Date(date);
                    weekendEnd = new Date(date);
                    weekendEnd.setDate(date.getDate() + 2); // Sunday
                } else {
                    // For other days, find the nearest weekend
                    const daysToFriday = (5 - dayOfWeek + 7) % 7;
                    weekendStart = new Date(date);
                    weekendStart.setDate(date.getDate() + daysToFriday);
                    weekendEnd = new Date(weekendStart);
                    weekendEnd.setDate(weekendStart.getDate() + 2); // Sunday
                }
                
                const startMonth = weekendStart.getMonth() + 1;
                const startDay = weekendStart.getDate();
                const endMonth = weekendEnd.getMonth() + 1;
                const endDay = weekendEnd.getDate();
                
                if (startMonth === endMonth) {
                    return `${startMonth.toString().padStart(2, '0')}-${startDay.toString().padStart(2, '0')} to ${endDay.toString().padStart(2, '0')}`;
                } else {
                    return `${startMonth.toString().padStart(2, '0')}-${startDay.toString().padStart(2, '0')} to ${endMonth.toString().padStart(2, '0')}-${endDay.toString().padStart(2, '0')}`;
                }
            } catch (e) {
                return 'Unknown Weekend';
            }
        }
        
        // Update weekend analytics display
        function updateWeekendAnalyticsDisplay(weekendStats) {
            const container = document.getElementById('round-analytics');
            console.log('updateWeekendAnalyticsDisplay called, container:', container);
            console.log('weekendStats:', weekendStats);
            if (!container) {
                console.log('round-analytics container not found!');
                return;
            }
            
            const weekends = Object.keys(weekendStats).sort((a, b) => {
                // Sort weekends chronologically
                if (a === 'Unknown Weekend') return 1;
                if (b === 'Unknown Weekend') return -1;
                
                // Extract dates for comparison
                const aDate = weekendStats[a].matchDate;
                const bDate = weekendStats[b].matchDate;
                
                if (aDate === 'Unknown' || bDate === 'Unknown') {
                    return a.localeCompare(b);
                }
                
                return new Date(aDate) - new Date(bDate);
            });
            
            let html = '<div class="round-analytics-grid">';
            
            weekends.forEach(weekend => {
                const stats = weekendStats[weekend];
                const winRate = stats.completedBets > 0 ? Math.round((stats.wonBets / stats.completedBets) * 100) : 0;
                const profitClass = stats.totalProfit >= 0 ? 'profit-positive' : 'profit-negative';
                const leaguesList = Array.from(stats.leagues).join(', ');
                
                html += `
                    <div class="round-card">
                        <div class="round-header">
                            <h4>${weekend}</h4>
                            <span class="round-status ${stats.activeBets > 0 ? 'active' : 'completed'}">
                                ${stats.activeBets > 0 ? 'Active' : 'Completed'}
                            </span>
                        </div>
                        <div class="weekend-info">
                            <div class="weekend-leagues">${leaguesList || 'Unknown Leagues'}</div>
                        </div>
                        <div class="round-stats">
                            <div class="stat-item">
                                <span class="stat-label">Bets:</span>
                                <span class="stat-value">${stats.totalBets}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Win Rate:</span>
                                <span class="stat-value">${winRate}%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Stake:</span>
                                <span class="stat-value">£${stats.totalStake.toFixed(2)}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Profit:</span>
                                <span class="stat-value ${profitClass}">£${stats.totalProfit.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        // Update performance summary
        function updatePerformanceSummary(weekendStats) {
            const container = document.getElementById('performance-summary-content');
            console.log('updatePerformanceSummary called, container:', container);
            console.log('weekendStats:', weekendStats);
            if (!container) {
                console.log('performance-summary-content container not found!');
                return;
            }
            
            const weekends = Object.keys(weekendStats);
            if (weekends.length === 0) {
                container.innerHTML = '<p>No betting data available yet.</p>';
                return;
            }
            
            // Calculate overall stats
            let totalBets = 0;
            let totalWonBets = 0;
            let totalStake = 0;
            let totalProfit = 0;
            let totalActiveBets = 0;
            let totalCompletedBets = 0;
            
            weekends.forEach(weekend => {
                const stats = weekendStats[weekend];
                totalBets += stats.totalBets;
                totalWonBets += stats.wonBets;
                totalStake += stats.totalStake;
                totalProfit += stats.totalProfit;
                totalActiveBets += stats.activeBets;
                totalCompletedBets += stats.completedBets;
            });
            
            const overallWinRate = totalCompletedBets > 0 ? Math.round((totalWonBets / totalCompletedBets) * 100) : 0;
            const avgProfitPerWeekend = weekends.length > 0 ? totalProfit / weekends.length : 0;
            const bestWeekend = weekends.reduce((best, weekend) => {
                if (!best || weekendStats[weekend].totalProfit > weekendStats[best].totalProfit) {
                    return weekend;
                }
                return best;
            }, null);
            const worstWeekend = weekends.reduce((worst, weekend) => {
                if (!worst || weekendStats[weekend].totalProfit < weekendStats[worst].totalProfit) {
                    return weekend;
                }
                return worst;
            }, null);
            
            const profitClass = totalProfit >= 0 ? 'profit-positive' : 'profit-negative';
            const avgProfitClass = avgProfitPerWeekend >= 0 ? 'profit-positive' : 'profit-negative';
            
            const html = `
                <div class="performance-grid">
                    <div class="performance-card">
                        <h4>Overall Statistics</h4>
                        <div class="performance-stats">
                            <div class="perf-stat">
                                <span class="perf-label">Total Weekends:</span>
                                <span class="perf-value">${weekends.length}</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Total Bets:</span>
                                <span class="perf-value">${totalBets}</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Win Rate:</span>
                                <span class="perf-value">${overallWinRate}%</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Total Stake:</span>
                                <span class="perf-value">£${totalStake.toFixed(2)}</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Total Profit:</span>
                                <span class="perf-value ${profitClass}">£${totalProfit.toFixed(2)}</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Avg Profit/Weekend:</span>
                                <span class="perf-value ${avgProfitClass}">£${avgProfitPerWeekend.toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="performance-card">
                        <h4>Weekend Performance</h4>
                        <div class="performance-stats">
                            <div class="perf-stat">
                                <span class="perf-label">Best Weekend:</span>
                                <span class="perf-value">${bestWeekend} (£${weekendStats[bestWeekend]?.totalProfit.toFixed(2) || '0.00'})</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Worst Weekend:</span>
                                <span class="perf-value">${worstWeekend} (£${weekendStats[worstWeekend]?.totalProfit.toFixed(2) || '0.00'})</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Active Bets:</span>
                                <span class="perf-value">${totalActiveBets}</span>
                            </div>
                            <div class="perf-stat">
                                <span class="perf-label">Completed Bets:</span>
                                <span class="perf-value">${totalCompletedBets}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        }

        // Test function to debug analytics
        function testAnalytics() {
            console.log('Testing analytics...');
            console.log('activeBets:', activeBets);
            console.log('completedBets:', completedBets);
            updateAnalytics();
        }
        
        // Make testAnalytics available globally
        window.testAnalytics = testAnalytics;

        // Show breakdown by type
        function showBreakdown(type) {
            // Remove active class from all breakdown tabs
            document.querySelectorAll('.breakdown-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Add active class to clicked tab
            event.target.classList.add('active');
            
            // Update breakdown display
            updateBetBreakdown(type);
        }

        // Update bet breakdown display
        function updateBetBreakdown(type = 'all') {
            const container = document.getElementById('bet-breakdown-list');
            let betsToShow = [];
            
            if (type === 'active') {
                betsToShow = activeBets;
            } else if (type === 'completed') {
                betsToShow = completedBets;
            } else {
                betsToShow = [...activeBets, ...completedBets];
            }
            
            if (betsToShow.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #6c757d; padding: 20px;">No bets to display</p>';
                return;
            }
            
            // Sort bets by date (newest first)
            betsToShow.sort((a, b) => new Date(b.date) - new Date(a.date));
            
            container.innerHTML = '';
            
            betsToShow.forEach(bet => {
                const betItem = document.createElement('div');
                betItem.className = 'breakdown-bet-item';
                
                // Use the profit value from database
                const profit = bet.profit !== undefined ? bet.profit : 
                              (bet.status === 'won' ? (bet.stake * bet.odds) - bet.stake : 
                               bet.status === 'lost' ? -bet.stake : 0);
                const profitClass = bet.status === 'won' ? 'profit-positive' : 
                                   bet.status === 'lost' ? 'profit-negative' : 'profit-pending';
                const profitText = bet.status === 'pending' ? 'Pending' : 
                                  bet.status === 'won' ? `+£${profit.toFixed(2)}` : 
                                  `-£${Math.abs(profit).toFixed(2)}`;
                
                const statusClass = bet.status === 'won' ? 'status-won' : 
                                   bet.status === 'lost' ? 'status-lost' : 'status-pending';
                const statusText = bet.status === 'won' ? 'Won' : 
                                  bet.status === 'lost' ? 'Lost' : 'Pending';
                
                const date = new Date(bet.date).toLocaleDateString();
                const time = new Date(bet.date).toLocaleTimeString();
                
                // Support both flat and nested structures
                const game = bet.game || bet.opportunity?.game || 'Unknown';
                const betTeam = bet.bet_team || bet.opportunity?.bet_team || 'Unknown';
                const betType = bet.bet_type || bet.opportunity?.bet_type || 'WIN';
                const strategy = bet.strategy || bet.opportunity?.strategy || 'Unknown';
                const league = bet.league || bet.opportunity?.league || 'Unknown';
                
                betItem.innerHTML = `
                    <div class="breakdown-bet-info">
                        <div class="breakdown-bet-title">${game}</div>
                        <div class="breakdown-bet-details">
                            <strong>${betTeam}</strong> - ${betType} (${strategy})
                        </div>
                        <div class="breakdown-bet-meta">
                            ${league} • ${date} ${time}
                        </div>
                    </div>
                    <div class="breakdown-bet-amounts">
                        <div class="breakdown-stake">£${bet.stake.toFixed(2)}</div>
                        <div class="breakdown-odds">@ ${bet.odds.toFixed(3)}</div>
                    </div>
                    <div>
                        <div class="breakdown-profit ${profitClass}">${profitText}</div>
                        <div class="breakdown-status ${statusClass}">${statusText}</div>
                    </div>
                `;
                
                container.appendChild(betItem);
            });
        }

        // Calculate P&L
        function calculatePnL() {
            const totalProfit = completedBets.reduce((sum, bet) => sum + bet.profit, 0);
            const pendingValue = activeBets.reduce((sum, bet) => sum + bet.stake, 0);
            
            alert(`P&L Summary:\\n\\nCompleted Bets Profit: £${totalProfit.toFixed(2)}\\nPending Bets Value: £${pendingValue.toFixed(2)}\\n\\nTotal Potential: £${(totalProfit + pendingValue).toFixed(2)}`);
        }

        // Clear all betting history
        async function clearAllHistory() {
            const totalBets = activeBets.length + completedBets.length;
            
            if (totalBets === 0) {
                alert('No betting history to clear!');
                return;
            }
            
            const confirmMessage = `Are you sure you want to clear ALL betting history?\\n\\nThis will delete:\\n• ${activeBets.length} active bets\\n• ${completedBets.length} completed bets\\n\\nThis action cannot be undone!`;
            
            if (confirm(confirmMessage)) {
                // Clear all data
                activeBets = [];
                completedBets = [];
                
                // Save to file
                await saveBets();
                
                // Update displays
                updateBetsDisplay();
                updateAnalytics();
                
                alert('✅ All betting history has been cleared successfully!');
            }
        }

        // Show error
        function showError(message) {
            const container = document.getElementById('opportunities');
            container.innerHTML = `
                <div class="error">
                    <h3>❌ Error Loading Opportunities</h3>
                    <p>${message}</p>
                </div>
            `;
        }
    </script>
</body>
</html>"""


@app.route('/api/opportunities')
def get_opportunities():
    """API endpoint to get real betting opportunities from prediction system"""
    try:
        print("API: Getting opportunities...")
        opportunities = get_real_opportunities()
        print(f"API: Found {len(opportunities)} opportunities")
        return jsonify(opportunities)
    except Exception as e:
        print(f"Error getting opportunities: {e}")
        import traceback
        traceback.print_exc()
        # Return empty list if there's an error
        return jsonify([])


@app.route('/api/bets', methods=['GET', 'POST'])
def handle_bets():
    """API endpoint to handle bets with database storage"""
    if request.method == 'GET':
        # Return all bets from database
        bets = get_all_bets()
        return jsonify(bets)
    elif request.method == 'POST':
        # Update all bets from client
        new_bets = request.json
        save_bets_to_db(new_bets)
        return jsonify({'success': True})


@app.route('/api/analytics')
def get_analytics():
    """API endpoint to get betting analytics"""
    try:
        analytics = storage.get_analytics()
        return jsonify(analytics)
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return jsonify({
            'total_bets': 0,
            'won_bets': 0,
            'lost_bets': 0,
            'pending_bets': 0,
            'win_rate': 0,
            'total_stake': 0,
            'total_profit': 0,
            'average_odds': 0,
            'roi': 0
        })


def open_browser():
    """Open the browser after a short delay to ensure the server is running"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open('http://localhost:5000')


def open_browser_once():
    """Open browser only once, even with Flask auto-reloader"""
    global _browser_opened
    if not _browser_opened:
        _browser_opened = True
        open_browser()


if __name__ == '__main__':
    # Check if this is the main process (not a reloader subprocess)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("Starting Football Betting Logger with Real Predictions...")
        print("Opening browser automatically...")
        print("Features:")
        print("   - Real predictions from your betting algorithm")
        print("   - All 5 major European leagues (Premier League, Bundesliga, La Liga, Ligue 1, Serie A)")
        print("   - Round numbers, match dates, and detailed reasoning")
        print("   - File-based storage (no browser cache)")
        print("   - Add bets with odds and stake amounts")
        print("   - Track bet results and calculate P&L")
        print("   - Beautiful, responsive web interface")
        print("\nYour predictions are powered by momentum, form, top-bottom, and home-away strategies!")

        # Start browser opening in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()

    app.run(debug=False, host='0.0.0.0', port=5000)
