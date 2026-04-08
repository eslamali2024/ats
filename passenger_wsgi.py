#!/usr/bin/env python
"""
Passenger WSGI Application Wrapper
For compatibility with cPanel's Passenger service
"""

import sys
import os

# Add the application directory to the path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Import the FastAPI app
from app.main import app

# The WSGI application object (required by Passenger)
application = app
