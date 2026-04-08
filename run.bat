@echo off
REM CV Analyzer Service Startup Script for Windows

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Download spacy model
echo Downloading spacy model...
python -m spacy download en_core_web_sm

REM Run the application
echo Starting CV Analyzer Service...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
