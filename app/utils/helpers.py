import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a timestamp to string."""
    return timestamp.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse a timestamp string to datetime."""
    return datetime.strptime(timestamp_str, format_str)


def convert_to_dict(obj: Any) -> Dict:
    """Convert an object to a dictionary."""
    if isinstance(obj, dict):
        return obj
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    elif hasattr(obj, "_asdict"):
        return obj._asdict()
    else:
        return {str(i): getattr(obj, i) for i in dir(obj) if not i.startswith("_") and not callable(getattr(obj, i))}


def is_market_open(current_time: Optional[datetime] = None, 
                   open_time_str: str = "09:00:00", 
                   close_time_str: str = "23:30:00") -> bool:
    """
    Check if the market is currently open.
    
    Args:
        current_time: Current time (defaults to now)
        open_time_str: Market open time (HH:MM:SS)
        close_time_str: Market close time (HH:MM:SS)
        
    Returns:
        Boolean indicating if the market is open
    """
    if current_time is None:
        current_time = datetime.now()
    
    # Parse open and close times
    open_time = datetime.strptime(open_time_str, "%H:%M:%S").time()
    close_time = datetime.strptime(close_time_str, "%H:%M:%S").time()
    
    # Check if current time is within market hours
    current_time_of_day = current_time.time()
    
    # Handle case where market closes after midnight
    if close_time < open_time:
        return current_time_of_day >= open_time or current_time_of_day <= close_time
    else:
        return open_time <= current_time_of_day <= close_time


def calculate_profit_loss(entry_price: float, 
                          exit_price: float, 
                          quantity: float, 
                          is_buy: bool) -> float:
    """
    Calculate profit or loss for a trade.
    
    Args:
        entry_price: Entry price
        exit_price: Exit price
        quantity: Quantity traded
        is_buy: Whether it was a buy (True) or sell (False) trade
        
    Returns:
        Profit (positive) or loss (negative) amount
    """
    if is_buy:
        return (exit_price - entry_price) * quantity
    else:
        return (entry_price - exit_price) * quantity


def json_serialize(obj: Any) -> Any:
    """Custom JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        return str(obj)


def to_json(data: Any) -> str:
    """Convert data to JSON string."""
    return json.dumps(data, default=json_serialize)


def from_json(json_str: str) -> Any:
    """Convert JSON string to data."""
    return json.loads(json_str)


def get_timeframe_delta(timeframe: str) -> timedelta:
    """
    Get timedelta for a timeframe.
    
    Args:
        timeframe: Time interval ('1m', '5m', '15m', '1h', '1d')
        
    Returns:
        Timedelta object
    """
    if timeframe == '1m':
        return timedelta(minutes=1)
    elif timeframe == '5m':
        return timedelta(minutes=5)
    elif timeframe == '15m':
        return timedelta(minutes=15)
    elif timeframe == '1h':
        return timedelta(hours=1)
    elif timeframe == '1d':
        return timedelta(days=1)
    else:
        raise ValueError(f"Unsupported timeframe: {timeframe}")


def get_next_timeframe(timestamp: datetime, timeframe: str) -> datetime:
    """
    Get the next timestamp for a given timeframe.
    
    Args:
        timestamp: Current timestamp
        timeframe: Time interval ('1m', '5m', '15m', '1h', '1d')
        
    Returns:
        Next timestamp
    """
    delta = get_timeframe_delta(timeframe)
    return timestamp + delta 