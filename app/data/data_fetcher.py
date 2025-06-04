import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import requests
import time
from typing import Optional, List, Dict, Any

from app.config.config import (
    GOLD_TICKER_GLOBAL, 
    GOLD_TICKER_MCX, 
    POLYGON_API_KEY, 
    POLYGON_GOLD_TICKER,
    POLYGON_BASE_URL
)
from app.data.database import price_data_crud, SessionLocal

logger = logging.getLogger(__name__)


class GoldDataFetcher:
    """Class for fetching gold price data from various sources."""
    
    def __init__(self):
        self.sources = {
            'XAUUSD': 'GC=F',  # Gold futures ticker - more reliable than XAUUSD=X
            'MCX': GOLD_TICKER_MCX,
            'POLYGON': POLYGON_GOLD_TICKER
        }
    
    def fetch_yahoo_finance_data(self, 
                                 ticker: str = 'GC=F', 
                                 period: str = "1d", 
                                 interval: str = "1m") -> pd.DataFrame:
        """
        Fetch gold price data from Yahoo Finance.
        
        Args:
            ticker: Yahoo Finance ticker symbol
            period: Time period to fetch ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', 'ytd', 'max')
            interval: Time interval ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
            
        Returns:
            DataFrame with price data
        """
        try:
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
            
            # Get data using yfinance download method (more reliable than Ticker)
            df = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                timeout=10  # Add timeout to avoid hanging requests
            )
            
            if df.empty:
                logger.warning(f"No data returned for {ticker} with period={period}, interval={interval}")
                return pd.DataFrame()
            
            # Rename columns to match our database schema
            df = df.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Add source and timeframe columns
            df['source'] = 'XAUUSD'
            df['timeframe'] = interval
            
            # Reset index to make timestamp a column
            df = df.reset_index()
            
            # If the index column is named 'Date' or 'Datetime', rename it to 'timestamp'
            if 'Date' in df.columns:
                df = df.rename(columns={'Date': 'timestamp'})
            elif 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'timestamp'})
            
            # Handle NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # For intervals without volume data, set a default value
            if 'volume' not in df.columns or df['volume'].isnull().all():
                df['volume'] = 0
            
            logger.info(f"Successfully fetched {len(df)} records for {ticker} ({interval})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data from Yahoo Finance for {ticker}: {e}")
            return pd.DataFrame()
    
    def fetch_polygon_data(self, interval: str = "1h") -> pd.DataFrame:
        """
        Fetch gold price data from Polygon.io Forex API.
        
        Args:
            interval: Time interval ('1m', '5m', '15m', '1h', '1d')
            
        Returns:
            DataFrame with price data
        """
        if not POLYGON_API_KEY:
            logger.error("Polygon API key not configured")
            return pd.DataFrame()
        
        try:
            # Add rate limiting to avoid 429 errors
            # Sleep for 1.2 seconds to stay under the 5 requests per minute limit for free tier
            time.sleep(1.2)
            
            # Convert our interval format to Polygon's format
            polygon_multiplier, polygon_timespan = self._convert_to_polygon_timeframe(interval)
            ticker = self.sources['POLYGON']  # Should be C:XAUUSD for XAU/USD forex pair
            
            # Calculate date range based on interval
            end_date = datetime.now()
            if interval in ['1m', '5m', '15m']:
                # For smaller intervals, get the last day
                start_date = end_date - timedelta(days=1)
            elif interval == '1h':
                # For hourly, get the last week
                start_date = end_date - timedelta(days=7)
            else:
                # For daily, get the last month
                start_date = end_date - timedelta(days=30)
            
            # Format dates for API
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Check if we're using a forex ticker (starts with C:)
            is_forex = ticker.startswith("C:")
            
            # Use appropriate endpoint based on the ticker type
            if is_forex:
                # Use the forex endpoint
                endpoint = f"/v2/aggs/ticker/{ticker}/range/{polygon_multiplier}/{polygon_timespan}/{start_date_str}/{end_date_str}"
                logger.info(f"Using Polygon.io Forex endpoint for {ticker}")
            else:
                # Use the standard aggregates endpoint
                endpoint = f"/v2/aggs/ticker/{ticker}/range/{polygon_multiplier}/{polygon_timespan}/{start_date_str}/{end_date_str}"
                logger.info(f"Using Polygon.io standard endpoint for {ticker}")
            
            # Construct API URL
            url = f"{POLYGON_BASE_URL}{endpoint}"
            
            # Add API key to query params
            params = {
                "apiKey": POLYGON_API_KEY,
                "sort": "asc",
                "limit": 5000  # Max limit for the API
            }
            
            # Make API request
            logger.info(f"Fetching data from Polygon.io: {url}")
            response = requests.get(url, params=params)
            
            # Check for rate limit errors
            if response.status_code == 429:
                logger.warning("Rate limit exceeded for Polygon.io API, waiting and retrying...")
                time.sleep(15)  # Wait 15 seconds before retrying
                response = requests.get(url, params=params)
            
            response.raise_for_status()  # Raise exception for HTTP errors
            
            # Parse response
            data = response.json()
            
            # Improved handling - we accept results as long as they exist, regardless of status
            if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
                results = data["results"]
                logger.info(f"Polygon.io returned {len(results)} records with status: {data.get('status', 'unknown')}")
                
                # Convert to DataFrame
                df = pd.DataFrame(results)
                
                # Rename Polygon columns to match our schema
                column_mapping = {
                    'o': 'open',
                    'h': 'high',
                    'l': 'low',
                    'c': 'close',
                    'v': 'volume',
                    't': 'timestamp'
                }
                df = df.rename(columns=column_mapping)
                
                # Convert timestamp (milliseconds) to datetime
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Add source and timeframe columns
                df['source'] = 'POLYGON'
                df['timeframe'] = interval
                
                # Ensure all required columns exist
                for col in ['open', 'high', 'low', 'close', 'timestamp']:
                    if col not in df.columns:
                        logger.warning(f"Missing column {col} in Polygon data")
                        return pd.DataFrame()
                
                # Volume might not be available for forex data, so handle it separately
                if 'volume' not in df.columns:
                    logger.info("Volume data not available from Polygon Forex API, using default value")
                    df['volume'] = 0
                
                logger.info(f"Successfully processed {len(df)} records from Polygon.io")
                return df
            else:
                # If we reach here, there was an issue with the response
                logger.warning(f"No valid results in Polygon.io response: {data}")
                
                # If we get an error with a forex ticker, try fetching available forex tickers
                if is_forex and "error" in data:
                    logger.info("Attempting to get available forex tickers from Polygon.io")
                    self._log_available_forex_tickers()
                
                return pd.DataFrame()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Polygon.io: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error processing Polygon.io data: {e}")
            return pd.DataFrame()
    
    def _log_available_forex_tickers(self):
        """
        Fetch and log available forex tickers from Polygon.io to help with debugging.
        """
        if not POLYGON_API_KEY:
            return
        
        try:
            # Construct API URL for forex tickers
            url = f"{POLYGON_BASE_URL}/v3/reference/tickers"
            
            # Add API key and filter for forex
            params = {
                "apiKey": POLYGON_API_KEY,
                "market": "fx",
                "active": "true",
                "limit": 100
            }
            
            # Make API request
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            
            if data.get("status") == "OK" and "results" in data:
                tickers = [ticker.get("ticker") for ticker in data["results"]]
                logger.info(f"Available forex tickers from Polygon.io: {tickers}")
                
                # Check if our configured ticker is in the list
                gold_tickers = [t for t in tickers if "XAU" in t or "GOLD" in t]
                if gold_tickers:
                    logger.info(f"Available gold-related forex tickers: {gold_tickers}")
                    
                    if POLYGON_GOLD_TICKER not in tickers:
                        logger.warning(f"Configured ticker {POLYGON_GOLD_TICKER} not found in available tickers")
                        if gold_tickers:
                            logger.info(f"Consider using one of these instead: {gold_tickers}")
            else:
                logger.warning("Failed to fetch available forex tickers")
        except Exception as e:
            logger.error(f"Error fetching available forex tickers: {e}")
    
    def _convert_to_polygon_timeframe(self, interval: str) -> tuple:
        """
        Convert our interval format to Polygon's multiplier and timespan.
        
        Args:
            interval: Our interval format ('1m', '5m', '15m', '1h', '1d')
            
        Returns:
            Tuple of (multiplier, timespan) for Polygon API
        """
        mapping = {
            '1m': (1, 'minute'),
            '5m': (5, 'minute'),
            '15m': (15, 'minute'),
            '1h': (1, 'hour'),
            '1d': (1, 'day')
        }
        
        if interval not in mapping:
            logger.warning(f"Unsupported interval {interval} for Polygon.io, falling back to 1h")
            return (1, 'hour')
            
        return mapping[interval]
    
    def fetch_alternative_gold_data(self, interval: str = "1h") -> pd.DataFrame:
        """
        Fallback method to fetch gold data when Yahoo Finance fails.
        This uses multiple potential gold tickers to find one that works.
        
        Args:
            interval: Time interval
            
        Returns:
            DataFrame with price data
        """
        # List of alternative gold tickers to try
        alt_tickers = ['GC=F', 'GLD', 'IAU', 'SGOL']
        
        for ticker in alt_tickers:
            try:
                logger.info(f"Trying alternative gold ticker: {ticker}")
                period = '1d' if interval in ['1m', '5m', '15m'] else '1mo'
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.5)
                
                df = yf.download(
                    tickers=ticker,
                    period=period,
                    interval=interval,
                    auto_adjust=True,
                    progress=False,
                    timeout=10  # Add timeout to avoid hanging requests
                )
                
                if not df.empty:
                    # Process as usual
                    df = df.rename(columns={
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume'
                    })
                    
                    df['source'] = 'XAUUSD'
                    df['timeframe'] = interval
                    df = df.reset_index()
                    
                    if 'Date' in df.columns:
                        df = df.rename(columns={'Date': 'timestamp'})
                    elif 'Datetime' in df.columns:
                        df = df.rename(columns={'Datetime': 'timestamp'})
                    
                    df = df.fillna(method='ffill').fillna(method='bfill')
                    if 'volume' not in df.columns or df['volume'].isnull().all():
                        df['volume'] = 0
                        
                    logger.info(f"Successfully fetched {len(df)} records using alternative ticker {ticker}")
                    return df
            except Exception as e:
                logger.warning(f"Failed with alternative ticker {ticker}: {e}")
                continue
        
        logger.error("All alternative tickers failed, returning empty DataFrame")
        return pd.DataFrame()
    
    def store_price_data(self, df: pd.DataFrame):
        """Store price data in the database."""
        if df.empty:
            logger.warning("No data to store")
            return
        
        try:
            db = SessionLocal()
            records_created = 0
            
            for _, row in df.iterrows():
                # Convert to dict
                row_dict = row.to_dict()
                
                # Handle datetime if needed
                if 'timestamp' not in row_dict and ('Datetime' in row_dict or 'Date' in row_dict):
                    if 'Datetime' in row_dict:
                        row_dict['timestamp'] = row_dict.pop('Datetime')
                    elif 'Date' in row_dict:
                        row_dict['timestamp'] = row_dict.pop('Date')
                
                # Remove any columns that don't match our model
                keys_to_remove = [k for k in row_dict.keys() 
                                  if k not in ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'source', 'timeframe']]
                for key in keys_to_remove:
                    row_dict.pop(key, None)
                
                # Ensure all required fields are present
                required_fields = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'source', 'timeframe']
                if all(field in row_dict for field in required_fields):
                    # Create price data record
                    price_data_crud.create(db, row_dict)
                    records_created += 1
                else:
                    missing = [field for field in required_fields if field not in row_dict]
                    logger.warning(f"Skipping record due to missing fields: {missing}")
            
            logger.info(f"Stored {records_created} price data records")
        except Exception as e:
            logger.error(f"Error storing price data: {e}")
        finally:
            db.close()
    
    def fetch_and_store_data(self, source: str = 'XAUUSD', period: str = "1d", interval: str = "1m"):
        """Fetch and store price data."""
        if source == 'XAUUSD':
            # First try Yahoo Finance
            df = self.fetch_yahoo_finance_data(self.sources[source], period, interval)
            
            # If Yahoo Finance fails, try alternative Yahoo tickers
            if df.empty:
                logger.warning(f"Primary Yahoo Finance source failed for {interval}, trying alternatives")
                df = self.fetch_alternative_gold_data(interval)
                
                # If all Yahoo Finance options fail, try Polygon.io as final fallback
                if df.empty and POLYGON_API_KEY:
                    logger.warning("All Yahoo Finance sources failed, trying Polygon.io")
                    df = self.fetch_polygon_data(interval)
                
            self.store_price_data(df)
        elif source == 'POLYGON':
            # Directly use Polygon.io
            df = self.fetch_polygon_data(interval)
            self.store_price_data(df)
        elif source == 'MCX':
            # Implementation for MCX data would go here
            # This might require a different API or data source
            logger.warning("MCX data fetching not implemented yet")
        else:
            logger.error(f"Unsupported data source: {source}")


# Sample usage
def update_price_data():
    """Update price data for all sources and timeframes."""
    fetcher = GoldDataFetcher()
    
    # Update global gold price data (XAUUSD)
    timeframes = {
        '1m': '1d',   # 1-minute data for the last day
        '5m': '5d',   # 5-minute data for the last 5 days
        '15m': '5d',  # 15-minute data for the last 5 days
        '1h': '60d',  # 1-hour data for the last 60 days
        '1d': '1y'    # Daily data for the last year
    }
    
    for interval, period in timeframes.items():
        logger.info(f"Fetching {interval} data for period {period}")
        fetcher.fetch_and_store_data(source='XAUUSD', period=period, interval=interval)
    
    # Update MCX gold price data (when implemented)
    # fetcher.fetch_and_store_data(source='MCX', period='1d', interval='1m')


if __name__ == "__main__":
    update_price_data() 