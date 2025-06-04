import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from app.data.database import SessionLocal, price_data_crud, indicator_crud, prediction_crud, trade_crud
from app.data.models import TradeAction
from app.models.price_prediction.lstm_model import LSTMPricePredictor
from app.config.config import RISK_REWARD_RATIO, STOP_LOSS_PERCENT

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    STRONG_BUY = 2
    BUY = 1
    NEUTRAL = 0
    SELL = -1
    STRONG_SELL = -2


class DecisionEngine:
    """Decision engine for generating buy/sell signals based on indicators and predictions."""
    
    def __init__(self):
        """Initialize the decision engine."""
        self.lstm_predictor = LSTMPricePredictor(window_size=60, prediction_horizon=12)
        
        # Load the model if available
        self.lstm_predictor.load_saved_model()
    
    def calculate_rsi_signal(self, rsi: float) -> SignalStrength:
        """
        Calculate signal based on RSI.
        
        Args:
            rsi: RSI value
            
        Returns:
            Signal strength enum
        """
        if rsi < 30:
            return SignalStrength.STRONG_BUY if rsi < 20 else SignalStrength.BUY
        elif rsi > 70:
            return SignalStrength.STRONG_SELL if rsi > 80 else SignalStrength.SELL
        else:
            return SignalStrength.NEUTRAL
    
    def calculate_macd_signal(self, macd: float, macd_signal: float, macd_hist: float) -> SignalStrength:
        """
        Calculate signal based on MACD.
        
        Args:
            macd: MACD line value
            macd_signal: MACD signal line value
            macd_hist: MACD histogram value
            
        Returns:
            Signal strength enum
        """
        if macd > macd_signal:
            # Bullish
            if macd_hist > 0 and macd_hist > 0.1 * abs(macd):
                return SignalStrength.STRONG_BUY
            else:
                return SignalStrength.BUY
        elif macd < macd_signal:
            # Bearish
            if macd_hist < 0 and abs(macd_hist) > 0.1 * abs(macd):
                return SignalStrength.STRONG_SELL
            else:
                return SignalStrength.SELL
        else:
            return SignalStrength.NEUTRAL
    
    def calculate_bollinger_signal(self, price: float, upper: float, lower: float, middle: float) -> SignalStrength:
        """
        Calculate signal based on Bollinger Bands.
        
        Args:
            price: Current price
            upper: Upper band
            lower: Lower band
            middle: Middle band (SMA)
            
        Returns:
            Signal strength enum
        """
        bandwidth = (upper - lower) / middle
        
        if price < lower:
            # Price below lower band - potential buy
            if bandwidth > 0.05:  # Wide bands - strong trend
                return SignalStrength.STRONG_BUY
            else:
                return SignalStrength.BUY
        elif price > upper:
            # Price above upper band - potential sell
            if bandwidth > 0.05:  # Wide bands - strong trend
                return SignalStrength.STRONG_SELL
            else:
                return SignalStrength.SELL
        else:
            # Price within bands
            if price < middle:
                return SignalStrength.BUY
            elif price > middle:
                return SignalStrength.SELL
            else:
                return SignalStrength.NEUTRAL
    
    def calculate_moving_average_signal(self, price: float, sma_20: float, sma_50: float) -> SignalStrength:
        """
        Calculate signal based on moving averages.
        
        Args:
            price: Current price
            sma_20: 20-period SMA
            sma_50: 50-period SMA
            
        Returns:
            Signal strength enum
        """
        price_vs_sma20 = price - sma_20
        price_vs_sma50 = price - sma_50
        sma20_vs_sma50 = sma_20 - sma_50
        
        if price > sma_20 and price > sma_50 and sma_20 > sma_50:
            # Strong uptrend
            return SignalStrength.STRONG_BUY
        elif price > sma_20 and price > sma_50:
            # Uptrend
            return SignalStrength.BUY
        elif price < sma_20 and price < sma_50 and sma_20 < sma_50:
            # Strong downtrend
            return SignalStrength.STRONG_SELL
        elif price < sma_20 and price < sma_50:
            # Downtrend
            return SignalStrength.SELL
        else:
            # Mixed signals
            return SignalStrength.NEUTRAL
    
    def calculate_prediction_signal(self, current_price: float, predicted_prices: List[float]) -> SignalStrength:
        """
        Calculate signal based on price predictions.
        
        Args:
            current_price: Current price
            predicted_prices: List of predicted prices
            
        Returns:
            Signal strength enum
        """
        # Calculate average predicted price
        avg_predicted = np.mean(predicted_prices)
        percent_change = (avg_predicted - current_price) / current_price * 100
        
        if percent_change > 1.5:
            return SignalStrength.STRONG_BUY
        elif percent_change > 0.5:
            return SignalStrength.BUY
        elif percent_change < -1.5:
            return SignalStrength.STRONG_SELL
        elif percent_change < -0.5:
            return SignalStrength.SELL
        else:
            return SignalStrength.NEUTRAL
    
    def generate_trade_signal(self, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Generate a trade signal for a specific timeframe.
        
        Args:
            timeframe: Time interval ('1m', '5m', '15m', '1h', '1d')
            
        Returns:
            Dictionary with trade signal details
        """
        try:
            db = SessionLocal()
            
            # Get latest price data with indicators
            price_data = price_data_crud.get_by_timeframe(db, timeframe, limit=500)
            
            if not price_data or len(price_data) < 60:
                logger.warning(f"Not enough price data for {timeframe} timeframe")
                return {"error": "Not enough data"}
            
            # Get the latest data point
            latest_price_data = price_data[0]
            latest_indicators = latest_price_data.indicators[0] if latest_price_data.indicators else None
            
            if not latest_indicators:
                logger.warning(f"No technical indicators for latest price data")
                return {"error": "No technical indicators"}
            
            # Get price prediction
            prediction_result = self.lstm_predictor.generate_predictions_for_timeframe(timeframe)
            
            if "error" in prediction_result:
                logger.warning(f"Error generating predictions: {prediction_result['error']}")
                prediction_signal = SignalStrength.NEUTRAL
            else:
                predicted_prices = [p['predicted_price'] for p in prediction_result['predictions']]
                prediction_signal = self.calculate_prediction_signal(
                    latest_price_data.close, predicted_prices
                )
            
            # Calculate signals from different indicators
            rsi_signal = self.calculate_rsi_signal(latest_indicators.rsi_14)
            
            macd_signal = self.calculate_macd_signal(
                latest_indicators.macd,
                latest_indicators.macd_signal,
                latest_indicators.macd_histogram
            )
            
            bollinger_signal = self.calculate_bollinger_signal(
                latest_price_data.close,
                latest_indicators.bollinger_upper,
                latest_indicators.bollinger_lower,
                latest_indicators.bollinger_middle
            )
            
            ma_signal = self.calculate_moving_average_signal(
                latest_price_data.close,
                latest_indicators.sma_20,
                latest_indicators.sma_50
            )
            
            # Calculate overall signal
            signals = [
                rsi_signal.value,
                macd_signal.value,
                bollinger_signal.value,
                ma_signal.value,
                prediction_signal.value
            ]
            
            # Weights (can be adjusted)
            weights = [0.2, 0.2, 0.2, 0.2, 0.2]
            
            weighted_signal = np.average(signals, weights=weights)
            
            # Determine final signal
            if weighted_signal > 1.0:
                trade_action = TradeAction.BUY
                signal_strength = "STRONG"
            elif weighted_signal > 0.2:
                trade_action = TradeAction.BUY
                signal_strength = "MODERATE"
            elif weighted_signal < -1.0:
                trade_action = TradeAction.SELL
                signal_strength = "STRONG"
            elif weighted_signal < -0.2:
                trade_action = TradeAction.SELL
                signal_strength = "MODERATE"
            else:
                trade_action = TradeAction.HOLD
                signal_strength = "NEUTRAL"
            
            # Calculate stop loss and take profit
            current_price = latest_price_data.close
            
            if trade_action == TradeAction.BUY:
                stop_loss = current_price * (1 - STOP_LOSS_PERCENT / 100)
                take_profit = current_price + (current_price - stop_loss) * RISK_REWARD_RATIO
            elif trade_action == TradeAction.SELL:
                stop_loss = current_price * (1 + STOP_LOSS_PERCENT / 100)
                take_profit = current_price - (stop_loss - current_price) * RISK_REWARD_RATIO
            else:
                stop_loss = None
                take_profit = None
            
            # Create signal result
            signal_result = {
                "timestamp": datetime.now(),
                "timeframe": timeframe,
                "current_price": current_price,
                "action": trade_action.value,
                "signal_strength": signal_strength,
                "weighted_signal": weighted_signal,
                "signals": {
                    "rsi": rsi_signal.name,
                    "macd": macd_signal.name,
                    "bollinger": bollinger_signal.name,
                    "moving_averages": ma_signal.name,
                    "prediction": prediction_signal.name
                },
                "indicators": {
                    "rsi_14": latest_indicators.rsi_14,
                    "macd": latest_indicators.macd,
                    "macd_signal": latest_indicators.macd_signal,
                    "macd_histogram": latest_indicators.macd_histogram,
                    "bollinger_upper": latest_indicators.bollinger_upper,
                    "bollinger_middle": latest_indicators.bollinger_middle,
                    "bollinger_lower": latest_indicators.bollinger_lower,
                    "sma_20": latest_indicators.sma_20,
                    "sma_50": latest_indicators.sma_50
                },
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "prediction": prediction_result if "error" not in prediction_result else None
            }
            
            return signal_result
            
        except Exception as e:
            logger.error(f"Error generating trade signal: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    def generate_all_timeframe_signals(self) -> Dict[str, Dict[str, Any]]:
        """
        Generate trade signals for all timeframes.
        
        Returns:
            Dictionary with trade signals for each timeframe
        """
        timeframes = ['1m', '5m', '15m', '1h', '1d']
        signals = {}
        
        for timeframe in timeframes:
            signals[timeframe] = self.generate_trade_signal(timeframe)
        
        return signals


if __name__ == "__main__":
    # Example usage
    engine = DecisionEngine()
    signal = engine.generate_trade_signal('1h')
    print(signal) 