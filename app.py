import uvicorn
import logging
from dotenv import load_dotenv
import os
import argparse
import atexit

from app.api.api import app
from app.config.config import API_HOST, API_PORT, LOG_LEVEL, LOG_FILE
from app.services.scheduler import scheduler_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Gold Analysis and Trading Platform")
    parser.add_argument("--host", type=str, default=API_HOST, help="Host to bind")
    parser.add_argument("--port", type=int, default=API_PORT, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--no-scheduler", action="store_true", help="Disable background scheduler")
    return parser.parse_args()


def main():
    args = parse_args()
    
    logger.info(f"Starting Gold Analysis and Trading Platform on {args.host}:{args.port}")
    
    # Start background scheduler
    if not args.no_scheduler:
        logger.info("Starting background scheduler")
        scheduler_service.setup_data_fetching_jobs()
        scheduler_service.start()
        
        # Register shutdown function
        atexit.register(scheduler_service.shutdown)
    else:
        logger.info("Background scheduler disabled")
    
    # Start the API server
    uvicorn.run(
        "app.api.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main() 