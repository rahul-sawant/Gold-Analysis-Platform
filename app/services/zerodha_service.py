from kiteconnect import KiteConnect
from kiteconnect import KiteTicker
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.config.config import (
    ZERODHA_API_KEY, 
    ZERODHA_API_SECRET, 
    ZERODHA_REDIRECT_URL,
    GOLD_TICKER_MCX
)
from app.data.database import SessionLocal, trade_crud
from app.data.models import Trade, TradeAction

logger = logging.getLogger(__name__)


class ZerodhaService:
    """Service for interacting with Zerodha's Kite Connect API."""
    
    def __init__(self):
        """Initialize Zerodha service."""
        self.api_key = ZERODHA_API_KEY
        self.api_secret = ZERODHA_API_SECRET
        self.redirect_url = ZERODHA_REDIRECT_URL
        
        self.kite = KiteConnect(api_key=self.api_key)
        self.ticker = None
        self.access_token = None
        
        # Store instrument IDs for quick lookup
        self.instruments = {}
    
    def get_login_url(self) -> str:
        """Get the login URL for Zerodha authentication."""
        return self.kite.login_url()
    
    def generate_session(self, request_token: str) -> Dict[str, Any]:
        """
        Generate a session using the request token.
        
        Args:
            request_token: Request token from Zerodha callback
            
        Returns:
            Dictionary with session information
        """
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            
            return {
                "status": "success",
                "data": data
            }
        except Exception as e:
            logger.error(f"Error generating Zerodha session: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        try:
            profile = self.kite.profile()
            return {
                "status": "success",
                "data": profile
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha profile: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_margins(self) -> Dict[str, Any]:
        """Get user margins."""
        try:
            margins = self.kite.margins()
            return {
                "status": "success",
                "data": margins
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha margins: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_holdings(self) -> Dict[str, Any]:
        """Get user holdings."""
        try:
            holdings = self.kite.holdings()
            return {
                "status": "success",
                "data": holdings
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha holdings: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_positions(self) -> Dict[str, Any]:
        """Get user positions."""
        try:
            positions = self.kite.positions()
            return {
                "status": "success",
                "data": positions
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha positions: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_historical_data(self, 
                            instrument_token: int, 
                            from_date: datetime, 
                            to_date: datetime, 
                            interval: str) -> Dict[str, Any]:
        """
        Get historical data for an instrument.
        
        Args:
            instrument_token: Zerodha instrument token
            from_date: Start date
            to_date: End date
            interval: Time interval ('minute', '3minute', '5minute', '10minute', '15minute', '30minute', 'hour', 'day')
            
        Returns:
            Dictionary with historical data
        """
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            return {
                "status": "success",
                "data": data
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha historical data: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def place_order(self, 
                    tradingsymbol: str, 
                    quantity: int, 
                    transaction_type: str, 
                    order_type: str = "MARKET",
                    price: float = 0, 
                    product: str = "CNC",
                    stop_loss: float = None,
                    take_profit: float = None) -> Dict[str, Any]:
        """
        Place an order.
        
        Args:
            tradingsymbol: Trading symbol (e.g., 'GOLD19AUGFUT')
            quantity: Order quantity
            transaction_type: Transaction type ('BUY' or 'SELL')
            order_type: Order type ('MARKET', 'LIMIT', 'SL', 'SL-M')
            price: Order price (for LIMIT orders)
            product: Product type ('CNC', 'MIS', 'NRML')
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Dictionary with order information
        """
        try:
            # Place main order
            order_params = {
                "tradingsymbol": tradingsymbol,
                "quantity": quantity,
                "transaction_type": transaction_type,
                "order_type": order_type,
                "product": product,
                "exchange": "MCX"  # For gold futures
            }
            
            if order_type == "LIMIT":
                order_params["price"] = price
            
            order_id = self.kite.place_order(variety="regular", **order_params)
            
            # Track the order in our database
            db = SessionLocal()
            
            trade_data = {
                "action": transaction_type,
                "price": price if order_type == "LIMIT" else 0,  # We'll update this later for market orders
                "quantity": quantity,
                "order_id": order_id,
                "status": "PENDING",
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "is_automated": True
            }
            
            trade_record = trade_crud.create(db, trade_data)
            
            # Place SL and TP orders if specified
            sl_order_id = None
            tp_order_id = None
            
            if stop_loss and transaction_type == "BUY":
                # Place stop loss for a buy order
                sl_params = {
                    "tradingsymbol": tradingsymbol,
                    "quantity": quantity,
                    "transaction_type": "SELL",
                    "order_type": "SL",
                    "price": stop_loss,
                    "trigger_price": stop_loss,
                    "product": product,
                    "exchange": "MCX"
                }
                sl_order_id = self.kite.place_order(variety="regular", **sl_params)
            
            if stop_loss and transaction_type == "SELL":
                # Place stop loss for a sell order
                sl_params = {
                    "tradingsymbol": tradingsymbol,
                    "quantity": quantity,
                    "transaction_type": "BUY",
                    "order_type": "SL",
                    "price": stop_loss,
                    "trigger_price": stop_loss,
                    "product": product,
                    "exchange": "MCX"
                }
                sl_order_id = self.kite.place_order(variety="regular", **sl_params)
            
            if take_profit and transaction_type == "BUY":
                # Place take profit for a buy order
                tp_params = {
                    "tradingsymbol": tradingsymbol,
                    "quantity": quantity,
                    "transaction_type": "SELL",
                    "order_type": "LIMIT",
                    "price": take_profit,
                    "product": product,
                    "exchange": "MCX"
                }
                tp_order_id = self.kite.place_order(variety="regular", **tp_params)
            
            if take_profit and transaction_type == "SELL":
                # Place take profit for a sell order
                tp_params = {
                    "tradingsymbol": tradingsymbol,
                    "quantity": quantity,
                    "transaction_type": "BUY",
                    "order_type": "LIMIT",
                    "price": take_profit,
                    "product": product,
                    "exchange": "MCX"
                }
                tp_order_id = self.kite.place_order(variety="regular", **tp_params)
            
            db.close()
            
            return {
                "status": "success",
                "data": {
                    "order_id": order_id,
                    "sl_order_id": sl_order_id,
                    "tp_order_id": tp_order_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error placing Zerodha order: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_order_history(self, order_id: str = None) -> Dict[str, Any]:
        """
        Get order history.
        
        Args:
            order_id: Optional order ID to get details for a specific order
            
        Returns:
            Dictionary with order history
        """
        try:
            if order_id:
                order_history = self.kite.order_history(order_id=order_id)
            else:
                order_history = self.kite.orders()
            
            return {
                "status": "success",
                "data": order_history
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha order history: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Dictionary with cancel result
        """
        try:
            result = self.kite.cancel_order(variety="regular", order_id=order_id)
            
            # Update order status in our database
            db = SessionLocal()
            trade = db.query(Trade).filter(Trade.order_id == order_id).first()
            
            if trade:
                trade_crud.update(db, trade, {"status": "CANCELLED"})
            
            db.close()
            
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            logger.error(f"Error cancelling Zerodha order: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_quote(self, instruments: List[str]) -> Dict[str, Any]:
        """
        Get market quotes.
        
        Args:
            instruments: List of instrument identifiers (e.g., ['MCX:GOLD19AUGFUT'])
            
        Returns:
            Dictionary with quotes
        """
        try:
            quotes = self.kite.quote(instruments)
            
            return {
                "status": "success",
                "data": quotes
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha quotes: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_instruments(self, exchange: str = None) -> Dict[str, Any]:
        """
        Get instruments.
        
        Args:
            exchange: Optional exchange to filter instruments
            
        Returns:
            Dictionary with instruments
        """
        try:
            instruments = self.kite.instruments(exchange=exchange)
            
            # Store in cache for quick lookup
            for instrument in instruments:
                self.instruments[instrument['tradingsymbol']] = instrument
            
            return {
                "status": "success",
                "data": instruments
            }
        except Exception as e:
            logger.error(f"Error fetching Zerodha instruments: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_instrument_id(self, tradingsymbol: str, exchange: str = "MCX") -> int:
        """
        Get instrument ID for a trading symbol.
        
        Args:
            tradingsymbol: Trading symbol
            exchange: Exchange
            
        Returns:
            Instrument ID
        """
        # Check if we have it in cache
        if tradingsymbol in self.instruments:
            return self.instruments[tradingsymbol]['instrument_token']
        
        # Otherwise fetch all instruments
        instruments = self.get_instruments(exchange)
        
        if instruments['status'] == 'error':
            logger.error(f"Error fetching instruments: {instruments['message']}")
            return None
        
        for instrument in instruments['data']:
            if instrument['tradingsymbol'] == tradingsymbol and instrument['exchange'] == exchange:
                return instrument['instrument_token']
        
        logger.warning(f"Instrument not found: {tradingsymbol} on {exchange}")
        return None
    
    def place_trade_from_signal(self, signal: Dict[str, Any], quantity: int, tradingsymbol: str = None) -> Dict[str, Any]:
        """
        Place a trade based on a signal.
        
        Args:
            signal: Signal dictionary from decision engine
            quantity: Quantity to trade
            tradingsymbol: Optional trading symbol (defaults to configured gold ticker)
            
        Returns:
            Dictionary with trade result
        """
        try:
            if 'error' in signal:
                return {
                    "status": "error",
                    "message": f"Invalid signal: {signal['error']}"
                }
            
            if not tradingsymbol:
                tradingsymbol = GOLD_TICKER_MCX.split(':')[1]  # Remove exchange prefix
            
            # Get action from signal
            action = signal['action']
            
            if action == TradeAction.HOLD.value:
                return {
                    "status": "info",
                    "message": "Signal suggests to HOLD, no trade executed"
                }
            
            # Place order
            transaction_type = "BUY" if action == TradeAction.BUY.value else "SELL"
            
            result = self.place_order(
                tradingsymbol=tradingsymbol,
                quantity=quantity,
                transaction_type=transaction_type,
                stop_loss=signal['stop_loss'],
                take_profit=signal['take_profit']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error placing trade from signal: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def start_websocket(self, instrument_tokens: List[int], on_tick=None, on_connect=None, on_close=None, on_error=None):
        """
        Start WebSocket connection for real-time data.
        
        Args:
            instrument_tokens: List of instrument tokens to subscribe to
            on_tick: Callback for tick data
            on_connect: Callback for connection event
            on_close: Callback for close event
            on_error: Callback for error event
        """
        try:
            self.ticker = KiteTicker(self.api_key, self.access_token)
            
            # Set callbacks
            if on_tick:
                self.ticker.on_ticks = on_tick
            if on_connect:
                self.ticker.on_connect = on_connect
            if on_close:
                self.ticker.on_close = on_close
            if on_error:
                self.ticker.on_error = on_error
            
            # Start the ticker
            self.ticker.connect()
            
            # Subscribe to tokens
            self.ticker.subscribe(instrument_tokens)
            self.ticker.set_mode(self.ticker.MODE_FULL, instrument_tokens)
            
        except Exception as e:
            logger.error(f"Error starting Zerodha WebSocket: {e}")
            raise
    
    def stop_websocket(self):
        """Stop WebSocket connection."""
        if self.ticker:
            self.ticker.close()


# Singleton instance
zerodha_service = ZerodhaService() 