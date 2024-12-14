#!/bin/bash
# Get current version
version=$(cat ring-api/src/api/version.py | grep __version__ | awk -F'"' '{print $2}') # version is an integer

# Increment version
version=$((version + 1))

# Update version in file
echo "__version__ = \"$version\"" > ring-api/src/api/version.py

# Bumped version
echo "Bumped version to $version"
commit_message="Bumped version to $version"

# Commit
git add ring-api/src/api/version.py
git commit -m "$commit_message"


echo "Deploying API"

source .env
cd ring-api
sam build
sam deploy --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides RingApiKey=$RING_API_KEY

echo "Deploying frontend"
cd ../frontend
npm run deploy
