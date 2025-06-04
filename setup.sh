#!/bin/bash

echo "Setting up Gold Analysis and Trading Platform..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.example .env
    echo "Please edit the .env file with your Zerodha API credentials and other settings."
fi

# Create directories
echo "Creating necessary directories..."
mkdir -p models
mkdir -p logs
mkdir -p app/frontend/build

# Initialize database
echo "Initializing database..."
python -c "from app.data.models import init_db; init_db()"

echo "Setup completed successfully!"
echo "To start the application, run: python app.py"
echo "The API will be available at http://localhost:8000" 