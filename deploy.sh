#!/bin/bash

# Default to prod if no environment specified
ENVIRONMENT=${1:-prod}

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

echo "Deploying to $ENVIRONMENT environment..."

# Get current version
version=$(cat ring-api/src/api/version.py | grep __version__ | awk -F'"' '{print $2}') # version is an integer

# Increment version
version=$((version + 1))

# Update version in file
echo "__version__ = \"$version\"" > ring-api/src/api/version.py

# Bumped version
echo "Bumped version to $version"
commit_message="Bumped version to $version ($ENVIRONMENT)"

echo "Deploying API to $ENVIRONMENT..."

cd ring-api
sam build
sam deploy --config-env $ENVIRONMENT --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides RingApiKey=$RING_API_KEY

echo "Deploying frontend to $ENVIRONMENT..."
cd ../frontend

# Set environment variables for frontend build
export VITE_API_KEY=$VITE_API_KEY
export VITE_ENVIRONMENT=$ENVIRONMENT
export VITE_API_URL=$VITE_API_URL

# Use environment-specific deployment
if [[ "$ENVIRONMENT" == "dev" ]]; then
    npm run deploy:dev
else
    npm run deploy:prod
fi

echo "Committing changes to git..."
cd ..
git add ring-api/src/api/version.py
git add frontend/public/version.json

git commit -m "deploy: bump versions ($ENVIRONMENT)"

echo "Pushing to GitHub..."
git push

echo "Deployment to $ENVIRONMENT completed successfully!"