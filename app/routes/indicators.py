"""Technical indicators API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.data.database import get_db
from app.data.database import technical_indicator_crud
from app.schemas.indicators import TechnicalIndicator

router = APIRouter()


@router.get("/", response_model=List[TechnicalIndicator])
def get_indicators(
    source: str = "XAUUSD",
    timeframe: str = "1h",
    indicator_type: Optional[str] = None,
    limit: int = Query(100, gt=0, le=1000),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get technical indicators for a specific source and timeframe within a date range."""
    # Default date range: last 7 days
    if not from_date:
        from_date = datetime.now() - timedelta(days=7)
    if not to_date:
        to_date = datetime.now()
    
    indicators = technical_indicator_crud.get_by_date_range(
        db, 
        source=source, 
        timeframe=timeframe,
        indicator_type=indicator_type,
        from_date=from_date, 
        to_date=to_date,
        limit=limit
    )
    return indicators


@router.get("/latest", response_model=List[TechnicalIndicator])
def get_latest_indicators(
    source: str = "XAUUSD",
    timeframe: str = "1h",
    db: Session = Depends(get_db)
):
    """Get the latest technical indicators for a specific source and timeframe."""
    latest = technical_indicator_crud.get_latest(db, source=source, timeframe=timeframe)
    if not latest:
        raise HTTPException(status_code=404, detail="Technical indicators not found")
    return latest 