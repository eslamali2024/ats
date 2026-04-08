#!/usr/bin/env python
"""
CV Analyzer Service - Startup Script
Runs the FastAPI application with Uvicorn
"""

import sys
import os
import uvicorn

if __name__ == "__main__":
    # Add the current directory to the path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,  # Enable auto-reload on code changes
        log_level="info"
    )
