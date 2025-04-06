#!/bin/bash

# Source the API key from root .env file
export VITE_API_KEY=$RING_API_KEY

echo "VITE_API_KEY=$VITE_API_KEY"

# Build the project
npm run build

# Sync the dist folder with the S3 bucket, setting appropriate cache headers
# Most assets can be cached for a long time since they have content hashes
aws s3 sync dist/ s3://vogelring.com \
  --exclude "*.html" \
  --exclude "version.json" \
  --exclude "sw.js" \
  --cache-control "public, max-age=31536000, immutable"

# Upload HTML files with no caching
aws s3 sync dist/ s3://vogelring.com \
  --include "*.html" \
  --cache-control "no-cache, no-store, must-revalidate"

# Upload version.json and service worker with no caching
aws s3 sync dist/ s3://vogelring.com \
  --include "version.json" \
  --include "sw.js" \
  --cache-control "no-cache, no-store, must-revalidate"

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E1JFMT0RGVCMKH --paths "/*"

echo "Deployment completed successfully!" 