#!/bin/bash

# CV Analyzer Service Startup Script

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/Scripts/activate  # For Windows, use: venv\Scripts\activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download spacy model
echo "Downloading spacy model..."
python -m spacy download en_core_web_sm

# Run the application
echo "Starting CV Analyzer Service..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
