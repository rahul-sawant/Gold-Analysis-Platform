import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import os
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from typing import Tuple, List, Dict, Any, Optional

from app.config.config import MODEL_PATH
from app.data.database import SessionLocal, price_data_crud

logger = logging.getLogger(__name__)


class LSTMPricePredictor:
    """LSTM model for predicting gold prices."""
    
    def __init__(self, window_size: int = 60, prediction_horizon: int = 12):
        """
        Initialize the LSTM price predictor.
        
        Args:
            window_size: Number of time steps to use for prediction (lookback)
            prediction_horizon: How many steps into the future to predict
        """
        self.window_size = window_size
        self.prediction_horizon = prediction_horizon
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
        # Ensure model directory exists
        os.makedirs(MODEL_PATH, exist_ok=True)
        
        # Model file path
        self.model_file = os.path.join(MODEL_PATH, 'lstm_gold_predictor.h5')
    
    def _prepare_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare the data for LSTM model training.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        # Ensure we have enough data
        if len(data) < self.window_size + self.prediction_horizon:
            raise ValueError(f"Not enough data points. Need at least {self.window_size + self.prediction_horizon}")
        
        # Extract features
        features = data[['close', 'sma_20', 'sma_50', 'rsi_14', 'macd', 'bollinger_upper', 'bollinger_lower']].dropna()
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(features)
        
        # Create sequences for LSTM
        X, y = [], []
        for i in range(len(scaled_data) - self.window_size - self.prediction_horizon):
            X.append(scaled_data[i:i + self.window_size])
            # Use only the close price for prediction
            y.append(scaled_data[i + self.window_size:i + self.window_size + self.prediction_horizon, 0])
        
        X, y = np.array(X), np.array(y)
        
        # Split into training and testing sets (80/20)
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        return X_train, X_test, y_train, y_test
    
    def build_model(self, input_shape: Tuple[int, int]):
        """
        Build the LSTM model.
        
        Args:
            input_shape: Shape of input data (window_size, num_features)
        """
        model = Sequential()
        
        # LSTM layers
        model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
        model.add(Dropout(0.2))
        
        model.add(LSTM(units=50, return_sequences=True))
        model.add(Dropout(0.2))
        
        model.add(LSTM(units=50))
        model.add(Dropout(0.2))
        
        # Output layer
        model.add(Dense(units=self.prediction_horizon))
        
        # Compile
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        self.model = model
        return model
    
    def train(self, data: pd.DataFrame, epochs: int = 100, batch_size: int = 32, validation_split: float = 0.2):
        """
        Train the LSTM model.
        
        Args:
            data: DataFrame with price data
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Validation data percentage
            
        Returns:
            Training history
        """
        try:
            # Prepare data
            X_train, X_test, y_train, y_test = self._prepare_data(data)
            
            # Build model if not already built
            if self.model is None:
                self.build_model((X_train.shape[1], X_train.shape[2]))
            
            # Callbacks for training
            callbacks = [
                EarlyStopping(patience=10, restore_best_weights=True),
                ModelCheckpoint(filepath=self.model_file, save_best_only=True)
            ]
            
            # Train the model
            history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=callbacks,
                verbose=1
            )
            
            # Evaluate on test data
            test_loss = self.model.evaluate(X_test, y_test)
            logger.info(f"Test loss: {test_loss}")
            
            # Save model
            self.model.save(self.model_file)
            logger.info(f"Model saved to {self.model_file}")
            
            return history
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def load_saved_model(self):
        """Load a previously saved model."""
        try:
            if os.path.exists(self.model_file):
                self.model = load_model(self.model_file)
                logger.info(f"Model loaded from {self.model_file}")
                return True
            else:
                logger.warning(f"Model file not found: {self.model_file}")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """
        Make predictions using the trained model.
        
        Args:
            data: DataFrame with price data (must include the window_size latest data points)
            
        Returns:
            Predicted prices
        """
        try:
            # Ensure model is loaded
            if self.model is None:
                if not self.load_saved_model():
                    raise ValueError("Model not trained or loaded")
            
            # Prepare features
            features = data[['close', 'sma_20', 'sma_50', 'rsi_14', 'macd', 'bollinger_upper', 'bollinger_lower']].tail(self.window_size)
            
            if len(features) < self.window_size:
                raise ValueError(f"Not enough data points. Need at least {self.window_size}")
            
            # Scale the data
            scaled_data = self.scaler.transform(features)
            
            # Reshape for LSTM [samples, time steps, features]
            X = np.array([scaled_data])
            
            # Make prediction
            scaled_prediction = self.model.predict(X)
            
            # Inverse transform the prediction (only for close price, which is the first feature)
            # Create a dummy array with same shape as the original features
            dummy = np.zeros((len(scaled_prediction[0]), features.shape[1]))
            # Put the predicted values in the first column (close price)
            dummy[:, 0] = scaled_prediction[0]
            # Inverse transform
            prediction = self.scaler.inverse_transform(dummy)[:, 0]
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def evaluate(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Evaluate the model on historical data.
        
        Args:
            data: DataFrame with price data
            
        Returns:
            Dictionary with evaluation metrics
        """
        try:
            # Prepare data
            X_train, X_test, y_train, y_test = self._prepare_data(data)
            
            # Ensure model is loaded
            if self.model is None:
                if not self.load_saved_model():
                    raise ValueError("Model not trained or loaded")
            
            # Make predictions on test data
            y_pred = self.model.predict(X_test)
            
            # Inverse transform
            # Create dummy arrays for inverse transformation
            dummy_test = np.zeros((len(y_test), X_test.shape[2]))
            dummy_pred = np.zeros((len(y_pred), X_test.shape[2]))
            
            # For each prediction horizon step
            metrics = {}
            for i in range(self.prediction_horizon):
                # Put the actual and predicted values in the first column (close price)
                dummy_test[:, 0] = y_test[:, i]
                dummy_pred[:, 0] = y_pred[:, i]
                
                # Inverse transform
                actual = self.scaler.inverse_transform(dummy_test)[:, 0]
                predicted = self.scaler.inverse_transform(dummy_pred)[:, 0]
                
                # Calculate metrics
                mse = mean_squared_error(actual, predicted)
                rmse = np.sqrt(mse)
                mae = mean_absolute_error(actual, predicted)
                r2 = r2_score(actual, predicted)
                
                metrics[f"horizon_{i+1}"] = {
                    "mse": mse,
                    "rmse": rmse,
                    "mae": mae,
                    "r2": r2
                }
            
            # Overall metrics (average across all horizons)
            metrics["overall"] = {
                "mse": np.mean([m["mse"] for m in metrics.values()]),
                "rmse": np.mean([m["rmse"] for m in metrics.values()]),
                "mae": np.mean([m["mae"] for m in metrics.values()]),
                "r2": np.mean([m["r2"] for m in metrics.values()])
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            raise
    
    def generate_predictions_for_timeframe(self, timeframe: str = '1h') -> Dict[str, Any]:
        """
        Generate predictions for a specific timeframe and store in database.
        
        Args:
            timeframe: Time interval ('1m', '5m', '15m', '1h', '1d')
            
        Returns:
            Dictionary with prediction results
        """
        try:
            db = SessionLocal()
            
            # Get latest price data with indicators
            price_data = price_data_crud.get_by_timeframe(db, timeframe, limit=500)
            
            if not price_data or len(price_data) < self.window_size:
                logger.warning(f"Not enough price data for {timeframe} timeframe")
                return {"error": "Not enough data"}
            
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
                    'timeframe': p.timeframe,
                    'sma_20': p.indicators[0].sma_20 if p.indicators else None,
                    'sma_50': p.indicators[0].sma_50 if p.indicators else None,
                    'rsi_14': p.indicators[0].rsi_14 if p.indicators else None,
                    'macd': p.indicators[0].macd if p.indicators else None,
                    'bollinger_upper': p.indicators[0].bollinger_upper if p.indicators else None,
                    'bollinger_lower': p.indicators[0].bollinger_lower if p.indicators else None
                } for p in price_data if p.indicators
            ])
            
            # Drop rows with NaN values
            price_df = price_df.dropna()
            
            # Ensure we have enough data
            if len(price_df) < self.window_size:
                logger.warning(f"Not enough price data with indicators for {timeframe} timeframe")
                return {"error": "Not enough data with indicators"}
            
            # Make prediction
            prediction = self.predict(price_df)
            
            # Last known price
            last_price = price_df.iloc[-1]['close']
            last_timestamp = price_df.iloc[-1]['timestamp']
            
            # Generate future timestamps
            future_timestamps = []
            for i in range(1, self.prediction_horizon + 1):
                if timeframe == '1m':
                    future_timestamps.append(last_timestamp + timedelta(minutes=i))
                elif timeframe == '5m':
                    future_timestamps.append(last_timestamp + timedelta(minutes=5*i))
                elif timeframe == '15m':
                    future_timestamps.append(last_timestamp + timedelta(minutes=15*i))
                elif timeframe == '1h':
                    future_timestamps.append(last_timestamp + timedelta(hours=i))
                elif timeframe == '1d':
                    future_timestamps.append(last_timestamp + timedelta(days=i))
            
            # Create prediction result
            prediction_result = {
                "model_name": "LSTM",
                "last_price": last_price,
                "last_timestamp": last_timestamp,
                "prediction_horizon": self.prediction_horizon,
                "timeframe": timeframe,
                "predictions": [
                    {
                        "timestamp": timestamp,
                        "predicted_price": price
                    } for timestamp, price in zip(future_timestamps, prediction)
                ]
            }
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return {"error": str(e)}
        finally:
            db.close()


if __name__ == "__main__":
    # Example usage
    predictor = LSTMPricePredictor(window_size=60, prediction_horizon=12)
    
    # For testing, you could load data from database and train the model
    # from app.data.database import get_db
    # db = next(get_db())
    # price_data = price_data_crud.get_by_timeframe(db, '1h', limit=1000)
    # Convert to dataframe, preprocess, and train... 