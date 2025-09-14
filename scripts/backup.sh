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

# Copy backup to shared directory for n8n access (if running on Pi)
if [ -d "/mnt/ssd/data/shared/vogelring-backups" ]; then
    echo "📋 Copying backup to shared directory for n8n..."
    cp "$BACKUP_DIR/vogelring_${TIMESTAMP}.sql.gz" "/mnt/ssd/data/shared/vogelring-backups/"
fi

# Create a backup of the entire data directory (excluding backups)
# Note: Using sudo to access Docker volume directories owned by container users
echo "📁 Creating data directory backup..."
sudo tar -czf "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz" \
    --exclude="$BACKUP_DIR" \
    --exclude="*.log" \
    --exclude="*/nginx_cache/*" \
    --exclude="*/postgres/pg_*" \
    --exclude="*/postgres/base/*" \
    --exclude="*/postgres/global/*" \
    --exclude="*/postgres/pg_logical/*" \
    --exclude="*/postgres/pg_multixact/*" \
    --exclude="*/postgres/pg_notify/*" \
    --exclude="*/postgres/pg_replslot/*" \
    --exclude="*/postgres/pg_serial/*" \
    --exclude="*/postgres/pg_snapshots/*" \
    --exclude="*/postgres/pg_stat/*" \
    --exclude="*/postgres/pg_stat_tmp/*" \
    --exclude="*/postgres/pg_subtrans/*" \
    --exclude="*/postgres/pg_tblspc/*" \
    --exclude="*/postgres/pg_twophase/*" \
    --exclude="*/postgres/pg_wal/*" \
    --exclude="*/postgres/pg_xact/*" \
    "${DATA_DIR:-./data}"

# Fix ownership of the backup file (make it accessible to the current user)
sudo chown "$(id -u):$(id -g)" "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz"

# Clean up old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "vogelring_*.sql.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "data_*.tar.gz" -mtime +7 -delete

# Display backup information
BACKUP_SIZE=$(du -h "$BACKUP_DIR/vogelring_${TIMESTAMP}.sql.gz" | cut -f1)
DATA_BACKUP_SIZE=$(du -h "$BACKUP_DIR/data_${TIMESTAMP}.tar.gz" | cut -f1)

echo ""
echo "✅ Backup completed successfully!"
echo "📊 Backup Information:"
echo "   Database backup: vogelring_${TIMESTAMP}.sql.gz ($BACKUP_SIZE)"
echo "   Data backup: data_${TIMESTAMP}.tar.gz ($DATA_BACKUP_SIZE)"
echo "   Location: $BACKUP_DIR"
echo ""
echo "📋 Available backups:"
ls -lh "$BACKUP_DIR"/*.gz 2>/dev/null || echo "   No backups found"