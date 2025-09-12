#!/bin/bash

# Vogelring application startup script

set -e

echo "Starting Vogelring application..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration before running again."
    exit 1
fi

# Build and start services
echo "Building and starting Docker services..."
docker-compose up --build -d

echo "Waiting for services to be healthy..."
sleep 10

# Check service health
echo "Checking service health..."
docker-compose ps

echo "Application started successfully!"
echo "Frontend: http://localhost"
echo "API: http://localhost/api"
echo "Health check: http://localhost/health"