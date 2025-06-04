import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

from app.data.database import SessionLocal, price_data_crud, indicator_crud

logger = logging.getLogger(__name__)


class TechnicalIndicatorCalculator:
    """Class for calculating technical indicators for price data."""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average (SMA)."""
        return prices.rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
        """Calculate Exponential Moving Average (EMA)."""
        return prices.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate Relative Strength Index (RSI)."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, pd.Series]:
        """Calculate Moving Average Convergence Divergence (MACD)."""
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return {
            "upper": upper_band,
            "middle": sma,
            "lower": lower_band
        }
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for a price dataframe."""
        # Ensure we have price data
        if df.empty:
            logger.warning("Empty dataframe provided for indicator calculation")
            return df
        
        # Calculate indicators
        close_prices = df['close']
        
        # SMA
        df['sma_20'] = TechnicalIndicatorCalculator.calculate_sma(close_prices, 20)
        df['sma_50'] = TechnicalIndicatorCalculator.calculate_sma(close_prices, 50)
        df['sma_200'] = TechnicalIndicatorCalculator.calculate_sma(close_prices, 200)
        
        # EMA
        df['ema_20'] = TechnicalIndicatorCalculator.calculate_ema(close_prices, 20)
        
        # RSI
        df['rsi_14'] = TechnicalIndicatorCalculator.calculate_rsi(close_prices, 14)
        
        # MACD
        macd_dict = TechnicalIndicatorCalculator.calculate_macd(close_prices)
        df['macd'] = macd_dict['macd']
        df['macd_signal'] = macd_dict['signal']
        df['macd_histogram'] = macd_dict['histogram']
        
        # Bollinger Bands
        bb_dict = TechnicalIndicatorCalculator.calculate_bollinger_bands(close_prices)
        df['bollinger_upper'] = bb_dict['upper']
        df['bollinger_middle'] = bb_dict['middle']
        df['bollinger_lower'] = bb_dict['lower']
        
        return df
    
    @staticmethod
    def update_indicators_in_db(source: str = 'XAUUSD', timeframe: str = '1h', limit: int = 500):
        """Update technical indicators in the database for the latest price data."""
        try:
            db = SessionLocal()
            
            # Get price data
            price_data = price_data_crud.get_by_timeframe(db, timeframe, limit)
            
            if not price_data:
                logger.warning(f"No price data found for {source}:{timeframe}")
                return
            
            # Convert to dataframe
            price_df = pd.DataFrame([
                {
                    'id': p.id,
                    'timestamp': p.timestamp,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'volume': p.volume if p.volume else 0,
                    'source': p.source,
                    'timeframe': p.timeframe
                } for p in price_data
            ])
            
            # Calculate indicators
            price_df = TechnicalIndicatorCalculator.calculate_all_indicators(price_df)
            
            # Store indicators in database
            for _, row in price_df.iterrows():
                price_data_id = row['id']
                
                # Check if indicator record already exists
                existing_indicator = indicator_crud.get_by_price_data(db, price_data_id)
                
                indicator_data = {
                    'price_data_id': price_data_id,
                    'timestamp': row['timestamp'],
                    'sma_20': row['sma_20'] if not np.isnan(row['sma_20']) else None,
                    'sma_50': row['sma_50'] if not np.isnan(row['sma_50']) else None,
                    'sma_200': row['sma_200'] if not np.isnan(row['sma_200']) else None,
                    'ema_20': row['ema_20'] if not np.isnan(row['ema_20']) else None,
                    'rsi_14': row['rsi_14'] if not np.isnan(row['rsi_14']) else None,
                    'macd': row['macd'] if not np.isnan(row['macd']) else None,
                    'macd_signal': row['macd_signal'] if not np.isnan(row['macd_signal']) else None,
                    'macd_histogram': row['macd_histogram'] if not np.isnan(row['macd_histogram']) else None,
                    'bollinger_upper': row['bollinger_upper'] if not np.isnan(row['bollinger_upper']) else None,
                    'bollinger_middle': row['bollinger_middle'] if not np.isnan(row['bollinger_middle']) else None,
                    'bollinger_lower': row['bollinger_lower'] if not np.isnan(row['bollinger_lower']) else None
                }
                
                if existing_indicator:
                    indicator_crud.update(db, existing_indicator, indicator_data)
                else:
                    indicator_crud.create(db, indicator_data)
            
            logger.info(f"Updated indicators for {len(price_df)} price records")
            
        except Exception as e:
            logger.error(f"Error updating indicators: {e}")
        finally:
            db.close()


if __name__ == "__main__":
    # Example usage
    TechnicalIndicatorCalculator.update_indicators_in_db() 