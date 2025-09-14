#!/bin/bash

# Vogelring application stop script

set -e

echo "Stopping Vogelring application..."

# Stop and remove containers
docker-compose down

echo "Application stopped successfully!"