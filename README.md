# Gold Analysis and Trading Platform

## Overview
The Gold Analysis and Trading Platform is a comprehensive solution for analyzing gold price movements, generating predictions, and executing trades via the Zerodha API.

## Features
- Historical gold price data collection and analysis
- Technical indicator calculation (SMA, EMA, RSI, MACD, Bollinger Bands)
- Machine learning-based price prediction using LSTM
- Trading signal generation
- Automated trading via Zerodha integration
- RESTful API for all functionality
- Modern React-based frontend

## Setup and Installation

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm (for frontend development)
- Zerodha account (optional, for trading functionality)
- Polygon.io API key (as fallback data source)

### Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gold-analysis-platform.git
cd gold-analysis-platform
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following variables:
```
# Database configuration
DATABASE_URL=sqlite:///./gold_trading.db

# Yahoo Finance ticker symbols
GOLD_TICKER_GLOBAL=GC=F
GOLD_TICKER_MCX=MCX:GOLD

# Polygon.io API (as fallback data source)
POLYGON_API_KEY=your_polygon_api_key_here
POLYGON_GOLD_TICKER=C:XAUUSD

# Zerodha API credentials (optional)
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_API_SECRET=your_zerodha_api_secret
ZERODHA_USER_ID=your_zerodha_user_id
ZERODHA_PASSWORD=your_zerodha_password
ZERODHA_PIN=your_zerodha_pin
ZERODHA_REDIRECT_URL=http://localhost:8000/api/v1/auth/zerodha/callback

# Other configuration
TRADING_ENABLED=False
```

5. Set up the database:
```bash
alembic upgrade head
```

6. Build the frontend:
```bash
cd app/frontend
npm install
npm run build
```

7. Run the application:
```bash
cd ../..  # Return to the root directory
python app.py
```

The application will be available at http://localhost:8000

## Data Sources

### Primary: Yahoo Finance
The platform uses Yahoo Finance (via yfinance) as the primary data source for gold price data.

### Fallback: Polygon.io
If Yahoo Finance fails to provide data, the platform will automatically fall back to using the Polygon.io API. The application uses Polygon.io's Forex API to fetch XAU/USD (Gold vs US Dollar) pricing data, which provides accurate gold price information.

To enable this fallback:
1. Sign up for a Polygon.io account at https://polygon.io/
2. Get your API key from your dashboard
3. Add your API key to the `.env` file as follows:
```
POLYGON_API_KEY=your_polygon_api_key_here
POLYGON_GOLD_TICKER=C:XAUUSD
```

The `C:XAUUSD` ticker represents Gold priced in US Dollars in the Polygon.io Forex API.

## API Endpoints

### Price Data
- GET `/api/v1/data/price` - Get historical price data
- POST `/api/v1/data/update` - Update price data

### Predictions
- GET `/api/v1/predict/{timeframe}` - Get price predictions

### Trading Signals
- GET `/api/v1/signals/{timeframe}` - Get trading signals
- GET `/api/v1/signals` - Get signals for all timeframes

### Zerodha Trading
- GET `/api/v1/auth/zerodha/login` - Get Zerodha login URL
- GET `/api/v1/auth/zerodha/callback` - OAuth callback
- GET `/api/v1/zerodha/profile` - Get user profile
- POST `/api/v1/zerodha/order` - Place an order
- And more...

## Development

### Frontend Development
```bash
cd app/frontend
npm start
```

### Running Tests
```bash
pytest
```

## License
This project is licensed under the MIT License - see the LICENSE file for details. 