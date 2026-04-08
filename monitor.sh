#!/bin/bash

#############################################################################
# CV Analyzer Service - Monitoring Script
# Check service health and restart if needed
#############################################################################

set -e

# Configuration
SERVICE_NAME="cv-analyzer"
HEALTH_URL="http://127.0.0.1:8001/health"
MAX_RETRIES=3
RETRY_DELAY=5
ALERT_EMAIL="admin@yourdomain.com"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

check_health() {
    if command -v curl &> /dev/null; then
        response=$(curl -s -m 5 "$HEALTH_URL" || echo "")
        
        if echo "$response" | grep -q "healthy"; then
            return 0
        else
            return 1
        fi
    else
        # Fallback: check if service is running
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            return 0
        else
            return 1
        fi
    fi
}

restart_service() {
    log "Attempting to restart service..."
    sudo systemctl restart "$SERVICE_NAME"
    sleep 10
}

send_alert() {
    local message="$1"
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "CV Analyzer Alert" "$ALERT_EMAIL"
    fi
}

# Main monitoring loop
log "Starting health check for $SERVICE_NAME"

for i in $(seq 1 $MAX_RETRIES); do
    if check_health; then
        log "Health check passed"
        exit 0
    else
        log "Health check attempt $i/$MAX_RETRIES failed"
        
        if [ $i -lt $MAX_RETRIES ]; then
            log "Retrying in $RETRY_DELAY seconds..."
            sleep $RETRY_DELAY
        fi
    fi
done

# All retries failed - restart service
log "All health checks failed - restarting service"
restart_service

# Check if service recovered
if check_health; then
    log "Service recovered after restart"
    send_alert "CV Analyzer service was restarted at $(date)"
else
    log "Service failed to recover after restart"
    send_alert "CRITICAL: CV Analyzer service is down and failed to restart at $(date)"
    exit 1
fi
