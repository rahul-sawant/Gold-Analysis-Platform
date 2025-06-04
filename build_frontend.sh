#!/bin/bash

# Script to build the React frontend for the Gold Analysis Platform

# Change to the frontend directory
cd app/frontend

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build the frontend
echo "Building frontend..."
npm run build

# Return to the project root
cd ../..

echo "Frontend build complete!"
echo "The build files are located in app/frontend/build"
echo "You can now run the application with 'python app.py' to serve both the API and frontend." 