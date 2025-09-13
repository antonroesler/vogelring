#!/bin/bash

# Vogelring Production Deployment Script
# Run this on the Raspberry Pi

set -e

echo "🚀 Starting Vogelring deployment..."

# Configuration
APP_DIR="/mnt/ssd/apps/vogelring"
DATA_DIR="/mnt/ssd/data/vogelring"
LOGS_DIR="/mnt/ssd/logs/vogelring"
BACKUP_DIR="/mnt/ssd/backups/vogelring"

# Create directories
echo "📁 Creating directories..."
sudo mkdir -p $DATA_DIR/postgres
sudo mkdir -p $DATA_DIR/nginx_cache
sudo mkdir -p $LOGS_DIR/nginx
sudo mkdir -p $BACKUP_DIR
sudo chown -R pi:pi $DATA_DIR $LOGS_DIR $BACKUP_DIR

# Clone or update repository
if [ -d "$APP_DIR" ]; then
    echo "📥 Updating repository..."
    cd $APP_DIR
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone https://github.com/your-username/vogelring.git $APP_DIR
    cd $APP_DIR
fi

# Build frontend (if needed)
echo "🏗️ Building frontend..."
if [ -d "frontend" ]; then
    cd frontend
    # Add frontend build commands here if needed
    cd ..
fi

# Copy production environment file
echo "⚙️ Setting up environment..."
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production file not found! Please create it with your production settings."
    exit 1
fi

# Build and start services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
docker-compose -f docker-compose.prod.yml --env-file .env.production ps

# Test local connectivity
echo "🧪 Testing local connectivity..."
curl -f http://localhost/health/ || echo "⚠️ Health check failed"
curl -f http://localhost/api/dashboard/summary || echo "⚠️ API test failed"

echo "✅ Deployment completed!"
echo ""
echo "Next steps:"
echo "1. Update Cloudflare tunnel configuration"
echo "2. Add DNS record for prod.vogelring.com"
echo "3. Configure Cloudflare Access policy"
echo "4. Test external access via https://prod.vogelring.com"