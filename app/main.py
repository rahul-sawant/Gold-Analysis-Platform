import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
from pathlib import Path

from app.routes import setup_routes
from app.database import setup_database
from app.services.scheduler import start_scheduler, stop_scheduler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='gold_trading.log',
    filemode='a'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Gold Analysis Platform",
    description="A platform for analyzing gold prices and making trading decisions",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Setup routes
setup_routes(app)

# Setup database
setup_database()

# Static files for the frontend
frontend_path = Path("frontend/dist")
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
else:
    logger.warning(f"Frontend static files not found at {frontend_path}")

# Serve frontend index.html for all unmatched routes (after API routes are registered)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # This route will catch all requests that don't match API routes
    # and serve the frontend index.html for client-side routing
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Frontend not built. Please run 'npm run build' in the frontend directory."}
        )

@app.on_event("startup")
def startup_event():
    """Startup event handler."""
    logger.info("Starting Gold Analysis Platform")
    
    # Start the scheduler
    start_scheduler()

@app.on_event("shutdown")
def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Gold Analysis Platform")
    
    # Stop the scheduler
    stop_scheduler()

# For local development
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 