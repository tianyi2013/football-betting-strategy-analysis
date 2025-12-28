"""
Quick script to manually add a bet to the database.
Usage: python add_bet_manual.py
"""
import sqlite3
from datetime import datetime

def add_bet():
    # Bayern Munich vs Mainz - December 14, 2025
    db_path = "ui/data_storage/betting_data.db"

    print("Adding bet to Bayern Munich vs Mainz (2025-12-14)")
    print("-" * 50)

    home_team = "Bayern Munich"
    away_team = "Mainz"
    game = f"{home_team} vs {away_team}"

    # Get bet details from user
    selection = input("Selection (Home/Draw/Away) [Home]: ").strip() or "Home"
    stake = input("Stake amount [10.0]: ").strip() or "10.0"
    odds = input("Odds [1.5]: ").strip() or "1.5"
    league = input("League [bundesliga_1]: ").strip() or "bundesliga_1"
    status = input("Status (won/lost/pending) [pending]: ").strip() or "pending"

    # Determine bet_team based on selection
    if selection.lower() == "home":
        bet_team = home_team
    elif selection.lower() == "away":
        bet_team = away_team
    else:
        bet_team = "Draw"

    # Calculate profit
    stake_float = float(stake)
    odds_float = float(odds)

    if status.lower() == "won":
        profit = round((odds_float - 1.0) * stake_float, 2)
    elif status.lower() == "lost":
        profit = round(-stake_float, 2)
    else:
        profit = 0.0

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert the bet
    cursor.execute("""
        INSERT INTO bets (
            placement_date, match_date, league, game,
            bet_team, bet_type, stake, odds, 
            status, profit, strategy, confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # placement_date
        "2025-12-14",  # match_date
        league,  # league
        game,  # game
        bet_team,  # bet_team
        "WIN",  # bet_type
        stake_float,  # stake
        odds_float,  # odds
        status,  # status
        profit,  # profit
        "manual",  # strategy
        0.75  # confidence (default)
    ))

    conn.commit()
    bet_id = cursor.lastrowid

    print(f"\n✓ Bet added successfully!")
    print(f"  Bet ID: {bet_id}")
    print(f"  Match: {game}")
    print(f"  Date: 2025-12-14")
    print(f"  League: {league}")
    print(f"  Bet Team: {bet_team}")
    print(f"  Stake: ${stake_float}")
    print(f"  Odds: {odds_float}")
    print(f"  Status: {status}")
    print(f"  Profit: ${profit}")

    conn.close()

if __name__ == "__main__":
    try:
        add_bet()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

