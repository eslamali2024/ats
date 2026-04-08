#!/bin/bash

#############################################################################
# CV Analyzer Service - Deployment Helper Script for cPanel
# This script handles common deployment tasks
#############################################################################

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="cv-analyzer"
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SERVICE_DIR/venv"
LOG_DIR="$SERVICE_DIR/logs"
USERNAME=${1:-$USER}

# Function to print section headers
print_header() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# Function to print messages
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to display usage
usage() {
    cat << EOF
CV Analyzer Service - Deployment Helper

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    install         Install service and dependencies
    start           Start the service
    stop            Stop the service
    restart         Restart the service
    status          Show service status
    logs            Tail application logs
    health          Check service health
    setup-systemd   Setup systemd service (requires sudo)
    deploy          Full deployment (install + systemd setup)
    update-deps     Update Python dependencies
    test            Test the service
    help            Show this message

Options:
    --username USER     Specify cPanel username (default: current user)
    --port PORT         Specify service port (default: 8001)

Examples:
    $0 install --username myusername
    $0 start
    $0 logs
    $0 setup-systemd --username myusername
    $0 deploy --username myusername

EOF
}

# Install function
cmd_install() {
    print_header "Installing CV Analyzer Service"
    
    print_info "Creating virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    print_success "pip upgraded"
    
    print_info "Installing dependencies..."
    pip install -r "$SERVICE_DIR/requirements.txt"
    print_success "Dependencies installed"
    
    print_info "Downloading spaCy model..."
    python -m spacy download en_core_web_sm
    print_success "spaCy model downloaded"
    
    print_info "Creating logs directory..."
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
    print_success "Logs directory created"
    
    if [ ! -f "$SERVICE_DIR/.env" ]; then
        print_info "Creating .env file..."
        cp "$SERVICE_DIR/.env.example" "$SERVICE_DIR/.env"
        print_success ".env file created - please edit with your configuration"
    fi
    
    deactivate
    print_success "Installation complete!"
}

# Start function
cmd_start() {
    print_header "Starting CV Analyzer Service"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_error "Service is already running"
        return 1
    fi
    
    if sudo systemctl start "$SERVICE_NAME"; then
        print_success "Service started successfully"
        sleep 2
        cmd_status
    else
        print_error "Failed to start service"
        return 1
    fi
}

# Stop function
cmd_stop() {
    print_header "Stopping CV Analyzer Service"
    
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        print_error "Service is not running"
        return 1
    fi
    
    if sudo systemctl stop "$SERVICE_NAME"; then
        print_success "Service stopped successfully"
    else
        print_error "Failed to stop service"
        return 1
    fi
}

# Restart function
cmd_restart() {
    print_header "Restarting CV Analyzer Service"
    
    if sudo systemctl restart "$SERVICE_NAME"; then
        print_success "Service restarted successfully"
        sleep 2
        cmd_status
    else
        print_error "Failed to restart service"
        return 1
    fi
}

# Status function
cmd_status() {
    print_header "Service Status"
    sudo systemctl status "$SERVICE_NAME" || true
}

# Logs function
cmd_logs() {
    print_header "Application Logs"
    
    if [ ! -f "$LOG_DIR/app.log" ]; then
        print_error "Log file not found: $LOG_DIR/app.log"
        return 1
    fi
    
    tail -f "$LOG_DIR/app.log"
}

# Health check function
cmd_health() {
    print_header "Service Health Check"
    
    local port=8001
    local url="http://127.0.0.1:$port/health"
    
    print_info "Checking service at $url..."
    
    if command -v curl &> /dev/null; then
        if curl -s "$url" | grep -q "healthy"; then
            print_success "Service is healthy!"
            curl -s "$url" | python -m json.tool 2>/dev/null || curl -s "$url"
        else
            print_error "Service responded but is not healthy"
            curl -s "$url"
        fi
    else
        print_error "curl not found - cannot check health"
        return 1
    fi
}

# Setup systemd function
cmd_setup_systemd() {
    print_header "Setting up systemd Service"
    
    if [ "$EUID" -ne 0 ]; then 
        print_error "This command requires sudo privileges"
        return 1
    fi
    
    local service_file="/etc/systemd/system/$SERVICE_NAME.service"
    
    print_info "Creating systemd service file..."
    
    cat > "$service_file" << EOF
[Unit]
Description=CV Analyzer FastAPI Service
Documentation=https://fastapi.tiangolo.com/
After=network.target

[Service]
Type=notify
User=$USERNAME
WorkingDirectory=$SERVICE_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=$VENV_DIR/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4 --log-level info

Restart=always
RestartSec=10
StartLimitInterval=60s
StartLimitBurst=3

KillMode=mixed
KillSignal=SIGTERM

NoNewPrivileges=true
PrivateTmp=true

LimitNOFILE=65535

StandardOutput=append:$LOG_DIR/app.log
StandardError=append:$LOG_DIR/error.log

TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Service file created at $service_file"
    
    print_info "Reloading systemd daemon..."
    systemctl daemon-reload
    
    print_info "Enabling service..."
    systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd service configured successfully!"
    print_info "Start the service with: sudo systemctl start $SERVICE_NAME"
}

# Update dependencies function
cmd_update_deps() {
    print_header "Updating Dependencies"
    
    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    print_info "Updating dependencies..."
    pip install --upgrade -r "$SERVICE_DIR/requirements.txt"
    
    print_info "Downloading latest spaCy model..."
    python -m spacy download en_core_web_sm
    
    deactivate
    print_success "Dependencies updated successfully!"
    print_info "Restart the service with: sudo systemctl restart $SERVICE_NAME"
}

# Test function
cmd_test() {
    print_header "Testing Installation"
    
    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    print_info "Testing imports..."
    python << PYTHON_EOF
import sys
try:
    from fastapi import FastAPI
    print("✓ FastAPI OK")
    import uvicorn
    print("✓ uvicorn OK")
    import pdfplumber
    print("✓ pdfplumber OK")
    import spacy
    print("✓ spaCy OK")
    nlp = spacy.load("en_core_web_sm")
    print("✓ spaCy model loaded")
    import numpy
    print("✓ NumPy OK")
    import sklearn
    print("✓ scikit-learn OK")
    print("\nAll dependencies verified successfully!")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
PYTHON_EOF
    
    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        deactivate
        return 1
    fi
    
    deactivate
}

# Deploy function (install + setup-systemd)
cmd_deploy() {
    print_header "Full Deployment"
    
    cmd_install
    
    if [ "$EUID" -eq 0 ]; then
        cmd_setup_systemd
        print_success "Deployment complete! Starting service..."
        cmd_start
    else
        print_info "To complete setup, run: sudo $0 setup-systemd --username $USERNAME"
    fi
}

# Main command processing
case "${1:-help}" in
    install)
        cmd_install
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    health)
        cmd_health
        ;;
    setup-systemd)
        cmd_setup_systemd
        ;;
    deploy)
        cmd_deploy
        ;;
    update-deps)
        cmd_update_deps
        ;;
    test)
        cmd_test
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
