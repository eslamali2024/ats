#!/bin/bash

#############################################################################
# Backup Script for CV Analyzer Service
# Run this periodically (e.g., via cron) to backup the service
#############################################################################

set -e

# Configuration
SERVICE_DIR="/home/username/public_html/cv-analyzer-service"
BACKUP_DIR="/home/username/backups/cv-analyzer"
BACKUP_RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="cv-analyzer-backup-$TIMESTAMP.tar.gz"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Starting CV Analyzer backup at $(date)"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
echo "Creating backup: $BACKUP_FILE"
cd "$SERVICE_DIR"

tar --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='logs' \
    --exclude='.env' \
    -czf "$BACKUP_DIR/$BACKUP_FILE" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup created successfully${NC}"
    ls -lh "$BACKUP_DIR/$BACKUP_FILE"
else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi

# Backup .env file separately (with restricted permissions)
if [ -f "$SERVICE_DIR/.env" ]; then
    echo "Backing up .env file..."
    cp "$SERVICE_DIR/.env" "$BACKUP_DIR/.env-$TIMESTAMP"
    chmod 600 "$BACKUP_DIR/.env-$TIMESTAMP"
    echo -e "${GREEN}✓ .env file backed up${NC}"
fi

# Clean old backups
echo "Cleaning old backups (keeping last $BACKUP_RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "cv-analyzer-backup-*.tar.gz" -mtime +$BACKUP_RETENTION_DAYS -delete
find "$BACKUP_DIR" -name ".env-*" -mtime +$BACKUP_RETENTION_DAYS -delete

echo -e "${GREEN}✓ Backup cleanup completed${NC}"
echo "Backup completed at $(date)"
