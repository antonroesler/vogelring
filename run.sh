#!/bin/bash

# Default to dev environment for local development
ENVIRONMENT=${1:-dev}

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Usage: $0 [dev|prod]"
    echo "Environment must be either 'dev' or 'prod'"
    exit 1
fi

# Load environment-specific configuration
if [[ ! -f ".env.${ENVIRONMENT}" ]]; then
    echo "Error: .env.${ENVIRONMENT} file not found!"
    echo "Please create .env.${ENVIRONMENT} based on .env.${ENVIRONMENT}.example"
    exit 1
fi

source ".env.${ENVIRONMENT}"

echo "Starting local development with $ENVIRONMENT environment configuration..."

cd ring-api
sam local start-api --port 3001 --parameter-overrides RingApiKey=$RING_API_KEY