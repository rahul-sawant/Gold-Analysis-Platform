"""Price data API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.data.database import get_db
from app.data.database import price_data_crud
from app.data.data_fetcher import update_price_data
from app.schemas.price_data import PriceData, PriceDataCreate

router = APIRouter()


@router.get("/latest", response_model=PriceData)
def get_latest_price(
    source: str = "XAUUSD",
    timeframe: str = "1h",
    db: Session = Depends(get_db)
):
    """Get the latest price data for a specific source and timeframe."""
    latest = price_data_crud.get_latest(db, source=source, timeframe=timeframe)
    if not latest:
        raise HTTPException(status_code=404, detail="Price data not found")
    return latest


@router.get("/", response_model=List[PriceData])
def get_price_data(
    source: str = "XAUUSD",
    timeframe: str = "1h",
    limit: int = Query(100, gt=0, le=1000),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get price data for a specific source and timeframe within a date range."""
    # Default date range: last 7 days
    if not from_date:
        from_date = datetime.now() - timedelta(days=7)
    if not to_date:
        to_date = datetime.now()
    
    price_data = price_data_crud.get_by_date_range(
        db, 
        source=source, 
        timeframe=timeframe, 
        from_date=from_date, 
        to_date=to_date,
        limit=limit
    )
    return price_data


@router.post("/update")
def trigger_update():
    """Manually trigger an update of price data."""
    try:
        update_price_data()
        return {"message": "Price data update initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update price data: {str(e)}") 