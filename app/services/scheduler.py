"""Scheduler for background tasks."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time

from app.data.data_fetcher import GoldDataFetcher, update_price_data

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def test_polygon_data_fetch():
    """Test function to fetch data directly from Polygon.io without Yahoo Finance fallback."""
    logger.info("Testing Polygon.io data fetch")
    fetcher = GoldDataFetcher()
    
    # Test different timeframes
    timeframes = ['1h', '1d']
    
    for interval in timeframes:
        logger.info(f"Fetching {interval} data from Polygon.io")
        df = fetcher.fetch_polygon_data(interval=interval)
        
        if not df.empty:
            logger.info(f"Successfully fetched {len(df)} records from Polygon.io for {interval}")
            # Store the data
            fetcher.store_price_data(df)
        else:
            logger.error(f"Failed to fetch data from Polygon.io for {interval}")


def start_scheduler():
    """Start the background scheduler."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    # Update price data every minute
    scheduler.add_job(update_price_data, 'interval', minutes=1, id='update_price_data')
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """Stop the background scheduler."""
    if not scheduler.running:
        logger.warning("Scheduler is not running")
        return

    scheduler.shutdown()
    logger.info("Scheduler shutdown")


if __name__ == "__main__":
    # For testing
    test_polygon_data_fetch() 