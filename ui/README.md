# 🎯 Football Betting Logger - Web Interface

A beautiful, modern web interface for the Football Betting Logger system with **real predictions** from your betting algorithm. Track betting opportunities, manage your bets, and calculate P&L with an intuitive user interface.

## ✨ Features

- **🎯 Real Predictions**: Live betting opportunities from your algorithm (momentum, form, top-bottom, home-away strategies)
- **🏆 All 5 Leagues**: Premier League, Bundesliga, La Liga, Ligue 1, Serie A
- **📅 Match Details**: Round numbers, match dates, and detailed reasoning
- **📊 My Bets**: Track your active bets and mark results
- **📈 Analytics**: View betting statistics and calculate P&L
- **💾 File Storage**: Persistent data storage (no browser cache)
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🎨 Modern UI**: Beautiful, intuitive interface

## 🚀 Quick Start

### **Start the Web Interface**
```bash
cd ui
python simple_app.py
```

The browser will open automatically to **http://localhost:5000**

## 🎮 How to Use

### 1. View Real Opportunities
- Go to the **🎯 Opportunities** tab
- See **real predictions** from your betting algorithm
- Each opportunity shows:
  - League and game
  - **Round number and match date**
  - Recommended team and bet type
  - **Confidence percentage** from your algorithm
  - **Detailed reasoning** from your strategies
  - **Strategy information** (momentum, form, etc.)

### 2. Add Bets
For each opportunity:
1. Enter the **odds** (e.g., 2.5)
2. Enter your **stake** amount (e.g., $50)
3. Choose an action:
   - **Add Bet**: Add to pending bets
   - **Add & Mark Won**: Add and immediately mark as won
   - **Add & Mark Lost**: Add and immediately mark as lost

### 3. Manage Bets
- Go to the **📊 My Bets** tab
- View all your active bets
- Mark bets as won or lost
- Track your betting history

### 4. View Analytics
- Go to the **📈 Analytics** tab
- See your betting statistics:
  - Total bets placed
  - Win rate percentage
  - Total stake amount
  - Total profit/loss
- Click **💰 Calculate P&L** for detailed analysis

## 🛠️ Technical Details

### Architecture
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla JS)
- **Backend**: Python Flask
- **Data**: JSON file storage (`ui/bets.json`, `ui/analytics.json`)
- **Integration**: Real-time connection to your prediction system

### File Structure
```
ui/
├── simple_app.py          # Main Flask application
├── bet_logger.py          # Core betting logic
├── auto_pnl_calculator.py # P&L calculation
├── bets.json             # Your betting data (auto-created)
├── analytics.json        # Analytics data (auto-created)
└── README.md             # This file
```

### API Endpoints
- `GET /api/opportunities` - Get real betting opportunities from your algorithm
- `GET /api/bets` - Get current bets
- `POST /api/bets` - Save bets to file
- `GET /api/analytics` - Get analytics

## 🎨 UI Features

### Real Prediction Integration
- **Live data** from your betting algorithm
- **Round numbers** and **match dates** displayed
- **Confidence scores** from your strategies
- **Detailed reasoning** for each recommendation
- **Strategy breakdown** (momentum, form, top-bottom, home-away)

### Modern Design
- **Gradient backgrounds** and smooth animations
- **Card-based layout** for easy scanning
- **Color-coded status** indicators
- **Responsive grid** that adapts to screen size

### File-Based Storage
- **Persistent data** - survives browser restarts
- **JSON file storage** - easy to backup and share
- **No browser cache** - data stored on your computer

## 🔧 Troubleshooting

### Common Issues

**"No betting opportunities found":**
- Check that your data files are in the correct location (`../data/`)
- Ensure upcoming games are available in your data files
- Check console output for error messages

**"Flask not found" error:**
```bash
pip install flask
```

**"Port 5000 already in use":**
- Change the port in `simple_app.py`: `app.run(port=5001)`

### Getting Help
1. Check the console output for error messages
2. Open browser developer tools (F12) for JavaScript errors
3. Ensure all data files are in the correct directory structure

## 🎯 Next Steps

1. **Start the web interface**: `python simple_app.py`
2. **Open your browser**: Automatically opens to http://localhost:5000
3. **View real predictions**: See opportunities from your algorithm
4. **Add some bets**: Use the Opportunities tab
5. **Track your results**: Use the My Bets tab
6. **Calculate P&L**: Use the Analytics tab

## 📊 Data Storage

Your betting data is stored in:
- **`ui/bets.json`** - All your bets (active and completed)
- **`ui/analytics.json`** - Analytics and statistics

This means your data persists between sessions and browser restarts!

---

**🎉 Enjoy your new betting logger with real predictions!**