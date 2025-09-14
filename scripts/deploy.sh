#!/bin/bash

# Vogelring Deployment Script for Raspberry Pi
set -e

echo "🚀 Starting Vogelring deployment..."

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create data directory if it doesn't exist
DATA_DIR=${DATA_DIR:-./data}
mkdir -p "$DATA_DIR/postgres"
mkdir -p "$DATA_DIR/backups"

echo "📁 Created data directories"

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "📋 Created .env file from template"
        echo "⚠️  Please edit .env file with your configuration before continuing"
        echo "   Especially set a secure DB_PASSWORD!"
        read -p "Press Enter to continue after editing .env file..."
    else
        echo "❌ No .env.example file found"
        exit 1
    fi
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose down --remove-orphans
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
timeout=300
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
    echo "📋 Service status:"
    docker-compose ps
    echo "📋 Logs:"
    docker-compose logs --tail=50
    exit 1
fi

# Display service information
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 Access URLs:"
echo "   Frontend: http://localhost:${HTTP_PORT:-80}"
echo "   API: http://localhost:${API_PORT:-8000}"
echo "   API Docs: http://localhost:${API_PORT:-8000}/swagger"
echo "   Health Check: http://localhost:${HTTP_PORT:-80}/health"
echo ""
echo "📁 Data stored in: $DATA_DIR"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update services: ./scripts/update.sh"
echo ""