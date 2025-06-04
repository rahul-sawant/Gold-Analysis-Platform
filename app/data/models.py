from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.config.config import DATABASE_URL

Base = declarative_base()

class TradeAction(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class PriceData(Base):
    """Model for storing historical gold price data."""
    __tablename__ = "price_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    source = Column(String, nullable=False)  # e.g., 'MCX', 'XAUUSD'
    timeframe = Column(String, nullable=False)  # e.g., '1m', '5m', '1h', '1d'
    
    indicators = relationship("TechnicalIndicator", back_populates="price_data")
    predictions = relationship("PricePrediction", back_populates="price_data")


class TechnicalIndicator(Base):
    """Model for storing calculated technical indicators."""
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    price_data_id = Column(Integer, ForeignKey("price_data.id"))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    
    # Common indicators
    sma_20 = Column(Float, nullable=True)
    sma_50 = Column(Float, nullable=True)
    sma_200 = Column(Float, nullable=True)
    ema_20 = Column(Float, nullable=True)
    rsi_14 = Column(Float, nullable=True)
    macd = Column(Float, nullable=True)
    macd_signal = Column(Float, nullable=True)
    macd_histogram = Column(Float, nullable=True)
    bollinger_upper = Column(Float, nullable=True)
    bollinger_middle = Column(Float, nullable=True)
    bollinger_lower = Column(Float, nullable=True)
    
    price_data = relationship("PriceData", back_populates="indicators")


class PricePrediction(Base):
    """Model for storing price predictions from different models."""
    __tablename__ = "price_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    price_data_id = Column(Integer, ForeignKey("price_data.id"))
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    model_name = Column(String, nullable=False)  # e.g., 'LSTM', 'RandomForest'
    
    predicted_price = Column(Float, nullable=False)
    prediction_timeframe = Column(String, nullable=False)  # e.g., '1h', '1d'
    confidence = Column(Float, nullable=True)
    
    recommended_action = Column(String, nullable=False)  # BUY, SELL, HOLD
    
    price_data = relationship("PriceData", back_populates="predictions")
    trades = relationship("Trade", back_populates="prediction")


class Trade(Base):
    """Model for storing trade records."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    prediction_id = Column(Integer, ForeignKey("price_predictions.id"), nullable=True)
    timestamp = Column(DateTime, index=True, default=datetime.utcnow)
    
    action = Column(String, nullable=False)  # BUY or SELL
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    order_id = Column(String, nullable=True)  # External order ID from broker
    status = Column(String, nullable=False)  # PENDING, COMPLETED, CANCELLED, REJECTED
    
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    exit_price = Column(Float, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    profit_loss = Column(Float, nullable=True)
    
    is_automated = Column(Boolean, default=True)
    notes = Column(String, nullable=True)
    
    prediction = relationship("PricePrediction", back_populates="trades")


# Initialize database
def init_db():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return engine 