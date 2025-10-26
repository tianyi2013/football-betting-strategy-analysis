# 🏆 Football Betting Strategy Analysis

A comprehensive Python application for analyzing football betting strategies using historical data from **5 major European leagues**. This unified system provides backtesting, performance analysis, strategy comparison, data cleansing, and betting predictions for Premier League, La Liga, Ligue 1, Serie A, and Bundesliga.

## 🚀 Quick Start

### 1. Setup Virtual Environment (Recommended)
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies
```bash
# Install core dependencies
pip install -r requirements-minimal.txt
```

### 3. Run Analysis

#### Option A: Using Batch Scripts (Windows - Auto-activates venv)
```bash
# Navigate to bin folder
cd bin

# Run predictions for all leagues
prediction.bat

# Or run data cleansing
cleansing.bat
```

#### Option B: Direct Command Line
```bash
# Get betting predictions for any league
python app/cli.py --league premier_league --command predict
python app/cli.py --league laliga_1 --command predict
python app/cli.py --league le_championnat --command predict
python app/cli.py --league serie_a --command predict
python app/cli.py --league bundesliga_1 --command predict

# Run backtest analysis
python app/cli.py --league premier_league --command backtest --top-n 3 --start-season 2020 --end-season 2024

# Clean data formats
python app/cli.py --league premier_league --command cleanse
```

#### Option C: Web Interface (UI Dashboard)
```bash
# Start the web interface
python ui/simple_app.py

# Then open http://localhost:5000 in your browser
```

## 📁 Project Structure

```
football_data/
├── bin/                        # 🔧 Batch scripts for automation
│   ├── prediction.bat         # Batch script for running predictions (auto-activates venv)
│   └── cleansing.bat          # Batch script for data cleansing
├── app/                        # 🚀 Unified Application
│   ├── __init__.py
│   └── cli.py                 # Command-line interface for the application
├── ui/                         # 💻 Web Interface
│   ├── __init__.py
│   ├── simple_app.py          # Flask web application for betting dashboard
│   ├── bets.json              # Legacy JSON storage (for reference)
│   └── data_storage/          # 📊 Database storage layer
│       ├── __init__.py
│       ├── database_models.py # SQLite database schema and repositories
│       ├── storage_adapter.py # Storage abstraction layer
│       ├── migration.py       # JSON to SQLite migration utilities
│       └── betting_data.db    # SQLite database (active)
├── analytics/                  # 📊 Analytics and data processing
│   ├── __init__.py
│   ├── league_analytics.py    # Core league table analysis
│   └── performance_metrics.py # Performance calculation utilities
├── strategies/                 # 🎯 Betting strategies
│   ├── __init__.py
│   ├── base_strategy.py       # Abstract base strategy class
│   ├── form_strategy.py       # Form-based strategy (3-game lookback)
│   ├── momentum_strategy.py   # Momentum-based strategy (3-game lookback)
│   ├── home_away_strategy.py  # Home-away strategy
│   └── top_bottom_strategy.py # Top-Bottom betting strategy
├── backtest/                   # 🔄 Backtesting functionality
│   ├── __init__.py
│   ├── backtest_runner.py     # Backtest execution
│   └── results_analyzer.py    # Results analysis and visualization
├── predictions/                # 🎯 Prediction functionality
│   ├── __init__.py
│   ├── betting_advisor.py     # Core betting advisor (4 strategies)
│   ├── waterfall_betting_advisor.py # Waterfall priority-based advisor
│   ├── next_round_predictor.py # Next round predictions
│   └── prediction_runner.py   # Prediction runner
├── data_processing/           # 🧹 Data processing
│   ├── __init__.py
│   └── data_cleaner.py        # Data cleansing utilities
├── data/                      # 📈 Data directory (5 leagues)
│   ├── premier_league/        # Premier League data (2000-2025)
│   ├── laliga_1/             # La Liga data (2000-2025)
│   ├── le_championnat/       # Ligue 1 data (2000-2025)
│   ├── serie_a/              # Serie A data (2000-2025)
│   └── bundesliga_1/         # Bundesliga data (2000-2025)
├── doc/                       # 📚 Documentation
│   └── (Markdown documentation files)
├── .backups/                  # 📦 Migration backups
├── requirements-minimal.txt   # 📦 Core dependencies
├── requirements.txt           # 📦 All dependencies
├── venv/                      # 🐍 Virtual environment
└── README.md                  # 📖 This file
```

## 🌍 Supported Leagues

The unified application supports **5 major European leagues**:

| League | Code | Display Name | Status |
|--------|------|--------------|--------|
| **Premier League** | `premier_league` | Premier League | ✅ Full Support |
| **La Liga** | `laliga_1` | La Liga | ✅ Full Support |
| **Ligue 1** | `le_championnat` | Ligue 1 | ✅ Full Support |
| **Serie A** | `serie_a` | Serie A | ✅ Full Support |
| **Bundesliga** | `bundesliga_1` | Bundesliga | ✅ Full Support |

## 🎯 Available Commands

### 1. Predictions (`--command predict`)
**Purpose**: Get betting predictions for the next round of games

```bash
# Premier League predictions
python app/cli.py --league premier_league --command predict

# La Liga predictions
python app/cli.py --league laliga_1 --command predict

# Ligue 1 predictions
python app/cli.py --league le_championnat --command predict

# Serie A predictions
python app/cli.py --league serie_a --command predict

# Bundesliga predictions
python app/cli.py --league bundesliga_1 --command predict
```

### 2. Backtest Analysis (`--command backtest`)
**Purpose**: Run backtests on various strategies

```bash
# Top-Bottom strategy
python app/cli.py --league premier_league --command backtest --top-n 3 --start-season 2020 --end-season 2024

# Home-Away strategy
python app/cli.py --league serie_a --command backtest --home-away --start-season 2020 --end-season 2024
```

### 3. Form Analysis (`--command form`)
**Purpose**: Run form-based betting analysis

```bash
python app/cli.py --league laliga_1 --command form --form-games 5 --form-threshold 0.6 --start-season 2020 --end-season 2024
```

### 4. Momentum Analysis (`--command momentum`)
**Purpose**: Run momentum-based betting analysis

```bash
python app/cli.py --league le_championnat --command momentum --lookback-games 5 --winning-momentum-threshold 0.2 --start-season 2020 --end-season 2024
```

### 5. Data Cleansing (`--command cleanse`)
**Purpose**: Clean and standardize data formats

```bash
python app/cli.py --league premier_league --command cleanse
```

### 6. League Analysis (`--command analyze`)
**Purpose**: Analyze league standings for a specific season

```bash
python app/cli.py --league bundesliga_1 --command analyze --end-season 2024
```

## 📊 Strategy Performance (2020-2024)

### Historical Performance by League (2020-2024)

#### ROI Performance
| League | Top-Bottom | Form | Momentum | Home-Away |
|--------|------------|------|----------|-----------|
| **Premier League** | +65.5% | +97.7% | +100.2% | -9.2% |
| **La Liga** | +63.4% | +76.3% | +72.6% | -3.1% |
| **Serie A** | +84.5% | +93.7% | +93.2% | -15.4% |
| **Ligue 1** | +72.4% | +74.3% | +85.1% | -9.6% |
| **Bundesliga** | +62.5% | +62.5% | +99.5% | +62.5% |

#### Win Rate Performance
| League | Top-Bottom | Form | Momentum | Home-Away |
|--------|------------|------|----------|-----------|
| **Premier League** | 63.3% | 58.7% | 56.5% | 43.2% |
| **La Liga** | 67.6% | 57.2% | 51.6% | 45.0% |
| **Serie A** | 66.8% | 61.0% | 56.5% | 40.7% |
| **Ligue 1** | 62.7% | 55.9% | 53.7% | 42.3% |
| **Bundesliga** | 65.2% | 55.8% | 56.3% | 45.1% |

*All strategies use 3-game lookback periods*

### Best Performing Strategies (3-Game Lookback)

1. **Premier League Momentum**: +100.2% ROI (2,501 bets, 56.5% win rate)
2. **Serie A Momentum**: +93.2% ROI (2,359 bets, 56.5% win rate)
3. **Serie A Form**: +93.7% ROI (1,953 bets, 61.0% win rate)
4. **Premier League Form**: +97.7% ROI (2,011 bets, 58.7% win rate)
5. **Bundesliga Momentum**: +99.5% ROI (1,940 bets, 56.3% win rate)
6. **Serie A Top-Bottom**: +84.5% ROI (990 bets, 66.8% win rate)
7. **Ligue 1 Momentum**: +85.1% ROI (2,350 bets, 53.7% win rate)
8. **La Liga Top-Bottom**: +63.4% ROI (932 bets, 67.6% win rate)

## 🎯 Strategy Overview

**Note**: All strategies use **3-game lookback periods** to match the prediction runner configuration for optimal performance.

### 1. Top-Bottom Strategy
The main strategy implemented in this system:

1. **FOR Bets**: Bet on top N teams from the previous season
2. **AGAINST Bets**: Bet against bottom N teams from the previous season (excluding relegated teams)

### 2. Form-Based Strategy (3-Game Lookback)
A dynamic strategy based on recent team performance:

1. **Form Calculation**: Analyzes last 3 games to calculate form score
2. **Good Form Bets**: Bet on teams with form score above threshold (0.6)
3. **Dynamic Selection**: Teams are selected based on recent performance, not historical rankings
4. **Performance**: +97.7% ROI, 58.7% win rate (Premier League - 2,011 bets)

### 3. Momentum-Based Strategy (3-Game Lookback)
A sophisticated strategy that capitalizes on team momentum and streaks:

1. **Momentum Calculation**: Analyzes consecutive wins/losses in recent 3 games
2. **Smart Bet Selection**: 
   - **Equal Momentum**: When both teams have similar momentum → Bet on DRAW
   - **Higher Momentum**: When one team has significantly higher momentum → Bet on that team
3. **Streak-Based Selection**: Teams are selected based on current momentum, not historical performance
4. **Performance**: +100.2% ROI, 56.5% win rate (Premier League - 2,501 bets)

### 4. Home-Away Strategy
A simple baseline strategy for comparison:

1. **Home Team Bets**: Bet on the home team to win in every match
2. **Baseline Performance**: Provides a reference point for evaluating other strategies

## 🎯 Prediction System

The system uses a **weighted approach** combining 4 proven strategies with **3-game lookback periods** for optimal performance:

### Strategy Weights (Based on Performance - 3-Game Lookback)
- **🏆 Momentum Strategy** (40% weight) - Best performer: +100.2% ROI, 56.5% win rate (Premier League)
- **🥈 Form Strategy** (30% weight) - Second best: +97.7% ROI, 58.7% win rate (Premier League)
- **🥉 Top-Bottom Strategy** (20% weight) - Third best: +84.5% ROI, 66.8% win rate (Serie A)
- **🏠 Home-Away Strategy** (10% weight) - Baseline: -9.2% ROI, 43.2% win rate (Premier League)

### How Predictions Work

1. **Strategy Analysis**: Each strategy analyzes the game and provides recommendations
2. **Weighted Scoring**: Combines all strategies using performance-based weights
3. **Final Recommendation**: Only recommends if confidence > 0
4. **Supporting Strategies**: Shows which strategies support the recommendation

## 📈 Example Results

### Premier League Predictions
```
🎯 PREMIER LEAGUE BETTING PREDICTOR
============================================================
📅 Current Date: 28/09/2025
🏆 Next Round: 6
📊 Total Games: 10
💰 Betting Opportunities: 6
🎯 Average Confidence: 12.7%
📅 Round Date: 27/09/2025
============================================================

🎲 BETTING RECOMMENDATIONS:
------------------------------------------------------------
 1. Tottenham vs Wolves
    🎯 FINAL RECOMMENDATION:
        💰 BET ON: Tottenham
        🎯 Confidence: 26.0%
        📝 Reason: Weighted recommendation based on 2 strategies
        🔍 Supporting: top_bottom: Home team top 3 vs away team bottom 20, home_away: Home team strong home record (50.0%) vs away team weak away record (0.0%)
```

### Serie A Predictions
```
🎯 SERIE A BETTING PREDICTOR
============================================================
📅 Current Date: 28/09/2025
🏆 Next Round: 5
📊 Total Games: 10
💰 Betting Opportunities: 5
🎯 Average Confidence: 10.0%
📅 Round Date: 27/09/2025
============================================================

🎲 BETTING RECOMMENDATIONS:
------------------------------------------------------------
 1. Juventus vs Atalanta
    🎯 FINAL RECOMMENDATION:
        💰 BET ON: Juventus
        🎯 Confidence: 10.0%
        📝 Reason: Weighted recommendation based on 1 strategies
        🔍 Supporting: home_away: Home team strong home record (100.0%) vs away team weak away record (50.0%)
```

## 🏗️ Architecture

### Command Line
- **`app/cli.py`**: Command-line interface supporting all 5 leagues

### Analytics Module
- **`league_analytics.py`**: Core data processing and league table generation
- **`performance_metrics.py`**: Performance calculation utilities

### Strategies Module
- **`base_strategy.py`**: Abstract base class for all strategies
- **`top_bottom_strategy.py`**: Implements the top-bottom betting strategy
- **`form_strategy.py`**: Implements the form-based betting strategy
- **`momentum_strategy.py`**: Implements the momentum-based betting strategy
- **`home_away_strategy.py`**: Implements the home-away betting strategy

### Backtest Module
- **`backtest_runner.py`**: Executes backtests and manages parameters
- **`results_analyzer.py`**: Analyzes and visualizes results

### Predictions Module
- **`betting_advisor.py`**: Core betting advisor with 4 proven strategies
- **`next_round_predictor.py`**: Next round prediction functionality
- **`prediction_runner.py`**: Main prediction runner

### Data Processing Module
- **`data_cleaner.py`**: Data cleansing and format standardization

## 📦 Requirements

### Virtual Environment Setup (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements-minimal.txt
```

### Core Dependencies
- **pandas** (data manipulation and analysis)
- **numpy** (numerical computing)

## 🔧 Advanced Usage

### Complete Workflow
```bash
# 1. Clean data first
python app/cli.py --league premier_league --command cleanse

# 2. Run backtest analysis
python app/cli.py --league premier_league --command backtest --top-n 3 --start-season 2020 --end-season 2024

# 3. Get predictions for next round
python app/cli.py --league premier_league --command predict
```

### Strategy Testing
```bash
# Test form strategy with custom parameters
python app/cli.py --league laliga_1 --command form --form-games 5 --form-threshold 0.6 --start-season 2023 --end-season 2023

# Test momentum strategy
python app/cli.py --league serie_a --command momentum --lookback-games 5 --winning-momentum-threshold 0.2 --start-season 2023 --end-season 2023
```

### League Analysis
```bash
# Analyze 2024 season for any league
python app/cli.py --league bundesliga_1 --command analyze --end-season 2024
```

## ⚠️ Disclaimer

This betting system is for **educational purposes only**. Always:
- **Do your own research**
- **Bet responsibly** 
- **Never bet more than you can afford to lose**
- **Consider all factors** (injuries, weather, team news, etc.)

The system provides **historical data-based recommendations** but cannot predict future outcomes with certainty.