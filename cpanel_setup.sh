#!/bin/bash

#############################################################################
# CV Analyzer Service - cPanel Setup Script
# This script automates the deployment of the CV Analyzer service on cPanel
#############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="cv-analyzer"
SERVICE_DIR="$(pwd)"
PYTHON_VERSION="python3"
VENV_DIR="$SERVICE_DIR/venv"
LOG_DIR="$SERVICE_DIR/logs"

echo -e "${GREEN}=== CV Analyzer Service Setup for cPanel ===${NC}"
echo ""

# Step 1: Check Python version
echo -e "${YELLOW}Step 1: Checking Python version...${NC}"
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi
PYTHON_VERSION_OUTPUT=$($PYTHON_VERSION --version)
echo -e "${GREEN}Found: $PYTHON_VERSION_OUTPUT${NC}"
echo ""

# Step 2: Create virtual environment
echo -e "${YELLOW}Step 2: Creating virtual environment...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    $PYTHON_VERSION -m venv "$VENV_DIR"
    echo -e "${GREEN}Virtual environment created at $VENV_DIR${NC}"
fi
echo ""

# Step 3: Activate virtual environment and upgrade pip
echo -e "${YELLOW}Step 3: Upgrading pip, setuptools, and wheel...${NC}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel
echo -e "${GREEN}pip upgraded successfully${NC}"
echo ""

# Step 4: Install dependencies
echo -e "${YELLOW}Step 4: Installing dependencies from requirements.txt...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}Dependencies installed successfully${NC}"
echo ""

# Step 5: Download spaCy model
echo -e "${YELLOW}Step 5: Downloading spaCy language model...${NC}"
python -m spacy download en_core_web_sm
echo -e "${GREEN}spaCy model downloaded${NC}"
echo ""

# Step 6: Create logs directory
echo -e "${YELLOW}Step 6: Creating logs directory...${NC}"
mkdir -p "$LOG_DIR"
chmod 755 "$LOG_DIR"
echo -e "${GREEN}Logs directory created${NC}"
echo ""

# Step 7: Create .env file if it doesn't exist
echo -e "${YELLOW}Step 7: Configuring environment...${NC}"
if [ ! -f "$SERVICE_DIR/.env" ]; then
    cp "$SERVICE_DIR/.env.example" "$SERVICE_DIR/.env"
    echo -e "${GREEN}.env file created from .env.example${NC}"
    echo -e "${YELLOW}Please edit .env with your configuration${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi
echo ""

# Step 8: Fix permissions
echo -e "${YELLOW}Step 8: Setting permissions...${NC}"
chmod 755 "$SERVICE_DIR"
chmod 755 "$VENV_DIR/bin"/*
chmod 644 "$SERVICE_DIR/requirements.txt"
echo -e "${GREEN}Permissions set${NC}"
echo ""

# Step 9: Test the installation
echo -e "${YELLOW}Step 9: Testing installation...${NC}"
python -c "
from fastapi import FastAPI
import uvicorn
import pdfplumber
import spacy
print('✓ FastAPI installed')
print('✓ uvicorn installed')
print('✓ pdfplumber installed')
print('✓ spaCy installed')
"
echo -e "${GREEN}All dependencies verified${NC}"
echo ""

echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your configuration:"
echo "   nano $SERVICE_DIR/.env"
echo ""
echo "2. Test the service locally:"
echo "   source $VENV_DIR/bin/activate"
echo "   uvicorn app.main:app --host 0.0.0.0 --port 8001"
echo ""
echo "3. For systemd service setup, see CPANEL_DEPLOYMENT_GUIDE.md"
echo ""
echo "4. Integrate with Laravel using the provided service class"
echo ""
