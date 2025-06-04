import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Zerodha API credentials
ZERODHA_API_KEY = os.getenv("ZERODHA_API_KEY", "")
ZERODHA_API_SECRET = os.getenv("ZERODHA_API_SECRET", "")
ZERODHA_USER_ID = os.getenv("ZERODHA_USER_ID", "")
ZERODHA_PASSWORD = os.getenv("ZERODHA_PASSWORD", "")
ZERODHA_PIN = os.getenv("ZERODHA_PIN", "")
ZERODHA_REDIRECT_URL = os.getenv("ZERODHA_REDIRECT_URL", "http://localhost:8000/api/v1/auth/zerodha/callback")

# Gold ticker symbols
GOLD_TICKER_MCX = os.getenv("GOLD_TICKER_MCX", "MCX:GOLD")  # For MCX Gold
GOLD_TICKER_GLOBAL = os.getenv("GOLD_TICKER_GLOBAL", "GC=F")  # Gold Futures for Yahoo Finance

# Polygon.io API configuration
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
POLYGON_GOLD_TICKER = os.getenv("POLYGON_GOLD_TICKER", "C:XAUUSD")  # XAU/USD (Gold) forex ticker for Polygon
POLYGON_BASE_URL = "https://api.polygon.io"

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gold_trading.db")

# Model parameters
MODEL_WINDOW_SIZE = int(os.getenv("MODEL_WINDOW_SIZE", "14"))  # Number of days for prediction window
MODEL_PATH = os.getenv("MODEL_PATH", "./models/")

# Trading parameters
TRADING_ENABLED = os.getenv("TRADING_ENABLED", "False").lower() == "true"
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "1"))  # In units
RISK_REWARD_RATIO = float(os.getenv("RISK_REWARD_RATIO", "1.5"))
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", "0.5"))

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "gold_trading.log")

# Trading time window (Indian market hours for MCX)
MARKET_OPEN_TIME = os.getenv("MARKET_OPEN_TIME", "09:00:00")
MARKET_CLOSE_TIME = os.getenv("MARKET_CLOSE_TIME", "23:30:00") 