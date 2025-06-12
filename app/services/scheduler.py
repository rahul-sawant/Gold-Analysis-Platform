"""Scheduler for background tasks."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time

from app.data.data_fetcher import GoldDataFetcher, update_price_data

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background scheduler service for data fetching and other tasks."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self._started = False
    
    def setup_data_fetching_jobs(self):
        """Set up background jobs for data fetching."""
        logger.info("Setting up data fetching jobs")
        
        # Update price data every minute during market hours
        self.scheduler.add_job(
            update_price_data, 
            'interval', 
            minutes=1, 
            id='update_price_data',
            replace_existing=True
        )
        
        # Test polygon data fetch job (runs once at startup)
        self.scheduler.add_job(
            test_polygon_data_fetch,
            'date',
            run_date=datetime.now(),
            id='test_polygon_fetch',
            replace_existing=True
        )
        
        logger.info("Data fetching jobs configured")
    
    def start(self):
        """Start the background scheduler."""
        if self._started:
            logger.warning("Scheduler is already running")
            return
        
        try:
            self.scheduler.start()
            self._started = True
            logger.info("Background scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def shutdown(self):
        """Stop the background scheduler."""
        if not self._started:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Background scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")
    
    @property
    def running(self):
        """Check if scheduler is running."""
        return self._started and self.scheduler.running


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


# Legacy functions for backward compatibility
def start_scheduler():
    """Start the background scheduler (legacy function)."""
    scheduler_service.start()


def stop_scheduler():
    """Stop the background scheduler (legacy function)."""
    scheduler_service.shutdown()


# Create the global scheduler service instance
scheduler_service = SchedulerService()

# Legacy scheduler object for backward compatibility
scheduler = scheduler_service.scheduler


if __name__ == "__main__":
    # For testing
    test_polygon_data_fetch() 