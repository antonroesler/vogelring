#!/bin/bash

# Vogelring Restore Script
set -e

# Configuration
BACKUP_DIR=${DATA_DIR:-./data}/backups
DB_CONTAINER="vogelring-postgres"
DB_NAME="vogelring"
DB_USER="vogelring"

echo "🔄 Starting restore process..."

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory not found: $BACKUP_DIR"
    exit 1
fi

# List available backups
echo "📋 Available database backups:"
ls -lt "$BACKUP_DIR"/vogelring_*.sql.gz 2>/dev/null || {
    echo "❌ No database backups found"
    exit 1
}

# Get backup file to restore
if [ -z "$1" ]; then
    echo ""
    echo "Usage: $0 <backup_filename>"
    echo "Example: $0 vogelring_20240312_143022.sql.gz"
    echo ""
    echo "Or use 'latest' to restore the most recent backup:"
    echo "Example: $0 latest"
    exit 1
fi

if [ "$1" = "latest" ]; then
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/vogelring_*.sql.gz 2>/dev/null | head -n1)
    if [ -z "$BACKUP_FILE" ]; then
        echo "❌ No backup files found"
        exit 1
    fi
    echo "📦 Using latest backup: $(basename "$BACKUP_FILE")"
else
    BACKUP_FILE="$BACKUP_DIR/$1"
    if [ ! -f "$BACKUP_FILE" ]; then
        echo "❌ Backup file not found: $BACKUP_FILE"
        exit 1
    fi
fi

# Confirm restore operation
echo ""
echo "⚠️  WARNING: This will replace all current data!"
echo "   Backup file: $(basename "$BACKUP_FILE")"
echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo "   Date: $(stat -c %y "$BACKUP_FILE")"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo "❌ Database container is not running. Starting services..."
    docker-compose up -d postgres
    
    # Wait for database to be ready
    echo "⏳ Waiting for database to be ready..."
    timeout=60
    counter=0
    while [ $counter -lt $timeout ]; do
        if docker exec "$DB_CONTAINER" pg_isready -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
            echo "✅ Database is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
    done
    
    if [ $counter -ge $timeout ]; then
        echo "❌ Database failed to start within $timeout seconds"
        exit 1
    fi
fi

# Create a backup of current data before restore
echo "💾 Creating backup of current data before restore..."
CURRENT_BACKUP="$BACKUP_DIR/pre_restore_$(date +"%Y%m%d_%H%M%S").sql"
docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" --clean --if-exists > "$CURRENT_BACKUP"
gzip "$CURRENT_BACKUP"
echo "✅ Current data backed up to: $(basename "$CURRENT_BACKUP").gz"

# Restore database
echo "🔄 Restoring database from backup..."
gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"

echo ""
echo "✅ Database restore completed successfully!"
echo ""
echo "🔄 Restarting services to ensure consistency..."
docker-compose restart api

# Wait for API to be healthy
echo "⏳ Waiting for API to be healthy..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:${API_PORT:-8000}/health >/dev/null 2>&1; then
        echo "✅ API is healthy"
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "⚠️  API health check timeout, but restore completed"
fi

echo ""
echo "🎉 Restore process completed!"
echo "📊 Service status:"
docker-compose ps