#!/bin/bash

# Vogelring Backup Script
set -e

# Configuration
BACKUP_DIR=${DATA_DIR:-./data}/backups
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="vogelring-postgres"
DB_NAME="vogelring"
DB_USER="vogelring"

echo "💾 Starting backup process..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo "❌ Database container is not running"
    exit 1
fi

# Create database backup
echo "📦 Creating database backup..."
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists > "$BACKUP_DIR/vogelring_${TIMESTAMP}.sql"

# Compress the backup
echo "🗜️  Compressing backup..."
gzip "$BACKUP_DIR/vogelring_${TIMESTAMP}.sql"

# Create a backup of the entire data directory (excluding backups)
echo "📁 Creating data directory backup..."
if sudo tar -czf "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz" \
    --exclude="$BACKUP_DIR" \
    --exclude="*.log" \
    "${DATA_DIR:-./data}" 2>/dev/null; then
    echo "✅ Data directory backup completed"
else
    echo "⚠️  Data directory backup failed (permissions), continuing with database backup only"
    # Remove the failed backup file if it exists
    rm -f "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz" 2>/dev/null || true
fi

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "vogelring_*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "data_*.tar.gz" -mtime +7 -delete

# Display backup information
BACKUP_SIZE=$(du -h "$BACKUP_DIR/vogelring_${TIMESTAMP}.sql.gz" | cut -f1)

echo ""
echo "✅ Backup completed successfully!"
echo "📊 Backup Information:"
echo "   Database backup: vogelring_${TIMESTAMP}.sql.gz ($BACKUP_SIZE)"

if [ -f "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz" ]; then
    DATA_BACKUP_SIZE=$(du -h "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz" | cut -f1)
    echo "   Data backup: data_${TIMESTAMP}.tar.gz ($DATA_BACKUP_SIZE)"
else
    echo "   Data backup: Not created (permissions issue)"
fi

echo "   Location: $BACKUP_DIR"
echo ""
echo "📋 Available backups:"
ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null || echo "   No backups found"