#!/bin/bash

# Vogelring Update Script
set -e

echo "🔄 Starting Vogelring update..."

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "❌ Services are not running. Please start them first with ./scripts/deploy.sh"
    exit 1
fi

# Create backup before update
echo "💾 Creating backup before update..."
./scripts/backup.sh

# Pull latest changes (if using git)
if [ -d .git ]; then
    echo "📥 Pulling latest changes..."
    git pull
fi

# Rebuild and restart services
echo "🔨 Rebuilding services..."
docker-compose build --no-cache

echo "🔄 Restarting services..."
docker-compose down
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
timeout=180
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        healthy_count=$(docker-compose ps | grep -c "healthy" || true)
        total_services=3
        
        if [ "$healthy_count" -eq "$total_services" ]; then
            echo "✅ All services are healthy!"
            break
        fi
    fi
    
    sleep 5
    counter=$((counter + 5))
    echo "   Waiting... ($counter/${timeout}s)"
done

if [ $counter -ge $timeout ]; then
    echo "❌ Services failed to become healthy within $timeout seconds"
    echo "🔄 Rolling back..."
    docker-compose down
    # Here you could implement rollback logic
    exit 1
fi

echo "🎉 Update completed successfully!"
docker-compose ps