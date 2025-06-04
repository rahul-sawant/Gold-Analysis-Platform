from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query, Path, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from pydantic import BaseModel
import os

from app.data.database import get_db
from app.data.data_fetcher import GoldDataFetcher, update_price_data
from app.data.indicators import TechnicalIndicatorCalculator
from app.models.price_prediction.lstm_model import LSTMPricePredictor
from app.models.decision.decision_engine import DecisionEngine
from app.services.zerodha_service import zerodha_service
from app.config.config import ZERODHA_REDIRECT_URL, GOLD_TICKER_MCX, TRADING_ENABLED

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Gold Analysis and Trading Platform",
    description="API for gold price analysis, prediction, and automated trading",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
gold_data_fetcher = GoldDataFetcher()
decision_engine = DecisionEngine()

# Create API router for all /api endpoints
api_router = APIRouter(prefix="/api/v1")

# Pydantic models for API
class TradeRequest(BaseModel):
    tradingsymbol: str
    quantity: int
    transaction_type: str
    order_type: str = "MARKET"
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class SignalTradeRequest(BaseModel):
    timeframe: str = "1h"
    quantity: int
    tradingsymbol: Optional[str] = None


# Background tasks
def fetch_and_process_data():
    """Background task to fetch and process data."""
    try:
        # Update price data
        update_price_data()
        
        # Calculate indicators for all timeframes
        timeframes = ['1m', '5m', '15m', '1h', '1d']
        for tf in timeframes:
            TechnicalIndicatorCalculator.update_indicators_in_db(timeframe=tf)
        
        logger.info("Data fetching and processing completed")
    except Exception as e:
        logger.error(f"Error in background data processing: {e}")


# Configure static files and frontend serving
frontend_build_path = os.path.join("app", "frontend", "build")
frontend_static_path = os.path.join("app", "frontend", "build", "static")

# Only mount the static directory if it exists
if os.path.exists(frontend_static_path):
    app.mount("/static", StaticFiles(directory=frontend_static_path), name="static")


# Root endpoint (non-API)
@app.get("/")
async def root():
    """Root endpoint - serves the React frontend."""
    index_path = os.path.join(frontend_build_path, "index.html")
    
    # If the frontend build exists, serve it, otherwise return API info
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "Gold Analysis and Trading Platform API"}


# API routes
@api_router.get("/data/price", tags=["Data"])
async def get_price_data(
    timeframe: str = Query("1h", description="Time interval (1m, 5m, 15m, 1h, 1d)"),
    limit: int = Query(100, description="Number of data points to return"),
    db: Session = Depends(get_db)
):
    """Get historical price data."""
    from app.data.database import price_data_crud
    
    try:
        price_data = price_data_crud.get_by_timeframe(db, timeframe, limit)
        
        if not price_data:
            return {"status": "error", "message": "No data found"}
        
        # Convert to dictionary
        result = []
        for p in price_data:
            result.append({
                "id": p.id,
                "timestamp": p.timestamp,
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume,
                "source": p.source,
                "timeframe": p.timeframe
            })
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error getting price data: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/data/indicators", tags=["Data"])
async def get_indicators(
    timeframe: str = Query("1h", description="Time interval (1m, 5m, 15m, 1h, 1d)"),
    limit: int = Query(100, description="Number of data points to return"),
    db: Session = Depends(get_db)
):
    """Get technical indicators."""
    from app.data.database import price_data_crud
    
    try:
        price_data = price_data_crud.get_by_timeframe(db, timeframe, limit)
        
        if not price_data:
            return {"status": "error", "message": "No data found"}
        
        # Convert to dictionary
        result = []
        for p in price_data:
            if not p.indicators:
                continue
                
            ind = p.indicators[0]
            result.append({
                "id": p.id,
                "timestamp": p.timestamp,
                "price": p.close,
                "sma_20": ind.sma_20,
                "sma_50": ind.sma_50,
                "sma_200": ind.sma_200,
                "ema_20": ind.ema_20,
                "rsi_14": ind.rsi_14,
                "macd": ind.macd,
                "macd_signal": ind.macd_signal,
                "macd_histogram": ind.macd_histogram,
                "bollinger_upper": ind.bollinger_upper,
                "bollinger_middle": ind.bollinger_middle,
                "bollinger_lower": ind.bollinger_lower
            })
        
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error getting indicators: {e}")
        return {"status": "error", "message": str(e)}


@api_router.post("/data/update", tags=["Data"])
async def update_data(background_tasks: BackgroundTasks):
    """Update price data and indicators."""
    try:
        # Add task to background
        background_tasks.add_task(fetch_and_process_data)
        
        return {"status": "success", "message": "Data update started in background"}
    except Exception as e:
        logger.error(f"Error starting data update: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/predict/{timeframe}", tags=["Prediction"])
async def predict_prices(
    timeframe: str = Path(..., description="Time interval (1m, 5m, 15m, 1h, 1d)")
):
    """Predict future prices."""
    try:
        predictor = LSTMPricePredictor()
        prediction_result = predictor.generate_predictions_for_timeframe(timeframe)
        
        return {"status": "success", "data": prediction_result}
    except Exception as e:
        logger.error(f"Error predicting prices: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/signals/{timeframe}", tags=["Trading"])
async def get_trading_signals(
    timeframe: str = Path(..., description="Time interval (1m, 5m, 15m, 1h, 1d)")
):
    """Get trading signals."""
    try:
        signal = decision_engine.generate_trade_signal(timeframe)
        
        return {"status": "success", "data": signal}
    except Exception as e:
        logger.error(f"Error getting trading signals: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/signals", tags=["Trading"])
async def get_all_trading_signals():
    """Get trading signals for all timeframes."""
    try:
        signals = decision_engine.generate_all_timeframe_signals()
        
        return {"status": "success", "data": signals}
    except Exception as e:
        logger.error(f"Error getting all trading signals: {e}")
        return {"status": "error", "message": str(e)}


# Zerodha API routes
@api_router.get("/auth/zerodha/login", tags=["Zerodha"])
async def zerodha_login():
    """Get Zerodha login URL."""
    try:
        login_url = zerodha_service.get_login_url()
        
        return {"status": "success", "data": {"login_url": login_url}}
    except Exception as e:
        logger.error(f"Error getting Zerodha login URL: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/auth/zerodha/callback", tags=["Zerodha"])
async def zerodha_callback(request_token: str = Query(..., description="Request token from Zerodha")):
    """Callback endpoint for Zerodha authentication."""
    try:
        result = zerodha_service.generate_session(request_token)
        
        return result
    except Exception as e:
        logger.error(f"Error in Zerodha callback: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/zerodha/profile", tags=["Zerodha"])
async def zerodha_profile():
    """Get Zerodha profile."""
    try:
        profile = zerodha_service.get_profile()
        
        return profile
    except Exception as e:
        logger.error(f"Error getting Zerodha profile: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/zerodha/margins", tags=["Zerodha"])
async def zerodha_margins():
    """Get Zerodha margins."""
    try:
        margins = zerodha_service.get_margins()
        
        return margins
    except Exception as e:
        logger.error(f"Error getting Zerodha margins: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/zerodha/holdings", tags=["Zerodha"])
async def zerodha_holdings():
    """Get Zerodha holdings."""
    try:
        holdings = zerodha_service.get_holdings()
        
        return holdings
    except Exception as e:
        logger.error(f"Error getting Zerodha holdings: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/zerodha/positions", tags=["Zerodha"])
async def zerodha_positions():
    """Get Zerodha positions."""
    try:
        positions = zerodha_service.get_positions()
        
        return positions
    except Exception as e:
        logger.error(f"Error getting Zerodha positions: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/zerodha/orders", tags=["Zerodha"])
async def zerodha_orders():
    """Get Zerodha orders."""
    try:
        orders = zerodha_service.get_order_history()
        
        return orders
    except Exception as e:
        logger.error(f"Error getting Zerodha orders: {e}")
        return {"status": "error", "message": str(e)}


@api_router.get("/zerodha/order/{order_id}", tags=["Zerodha"])
async def zerodha_order(order_id: str = Path(..., description="Order ID")):
    """Get Zerodha order details."""
    try:
        order = zerodha_service.get_order_history(order_id)
        
        return order
    except Exception as e:
        logger.error(f"Error getting Zerodha order: {e}")
        return {"status": "error", "message": str(e)}


@api_router.post("/zerodha/order", tags=["Zerodha"])
async def place_zerodha_order(trade_request: TradeRequest):
    """Place a Zerodha order."""
    try:
        if not TRADING_ENABLED:
            return {"status": "error", "message": "Trading is disabled in configuration"}
        
        result = zerodha_service.place_order(
            tradingsymbol=trade_request.tradingsymbol,
            quantity=trade_request.quantity,
            transaction_type=trade_request.transaction_type,
            order_type=trade_request.order_type,
            price=trade_request.price if trade_request.price else 0,
            stop_loss=trade_request.stop_loss,
            take_profit=trade_request.take_profit
        )
        
        return result
    except Exception as e:
        logger.error(f"Error placing Zerodha order: {e}")
        return {"status": "error", "message": str(e)}


@api_router.delete("/zerodha/order/{order_id}", tags=["Zerodha"])
async def cancel_zerodha_order(order_id: str = Path(..., description="Order ID")):
    """Cancel a Zerodha order."""
    try:
        if not TRADING_ENABLED:
            return {"status": "error", "message": "Trading is disabled in configuration"}
        
        result = zerodha_service.cancel_order(order_id)
        
        return result
    except Exception as e:
        logger.error(f"Error cancelling Zerodha order: {e}")
        return {"status": "error", "message": str(e)}


@api_router.post("/zerodha/trade/signal", tags=["Zerodha"])
async def place_trade_from_signal(trade_request: SignalTradeRequest):
    """Place a trade based on a signal."""
    try:
        if not TRADING_ENABLED:
            return {"status": "error", "message": "Trading is disabled in configuration"}
        
        # Get signal
        signal = decision_engine.generate_trade_signal(trade_request.timeframe)
        
        # Place trade
        result = zerodha_service.place_trade_from_signal(
            signal=signal,
            quantity=trade_request.quantity,
            tradingsymbol=trade_request.tradingsymbol
        )
        
        return result
    except Exception as e:
        logger.error(f"Error placing trade from signal: {e}")
        return {"status": "error", "message": str(e)}


# Include the API router
app.include_router(api_router)


# This catch-all route should be at the end to serve the frontend for any non-API routes
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    """Serve frontend paths for client-side routing."""
    index_path = os.path.join(frontend_build_path, "index.html")
    
    # If the frontend build exists, serve the index.html
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="Frontend not built")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 