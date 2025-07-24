#!/bin/bash

# Development frontend deployment script

# Build the project with dev environment variables
npm run build

S3_BUCKET=dev.vogelring.com
CLOUDFRONT_DISTRIBUTION_ID=E3O9WK7UJK93H1

# Sync the dist folder with the dev S3 bucket
# Most assets can be cached for a long time since they have content hashes
aws s3 sync dist/ s3://${S3_BUCKET} \
  --exclude "*.html" \
  --exclude "version.json" \
  --exclude "sw.js" \
  --cache-control "public, max-age=31536000, immutable"

# Upload HTML files with no caching
aws s3 sync dist/ s3://${S3_BUCKET} \
  --include "*.html" \
  --cache-control "no-cache, no-store, must-revalidate"

# Upload version.json and service worker with no caching
aws s3 sync dist/ s3://${S3_BUCKET} \
  --include "version.json" \
  --include "sw.js" \
  --cache-control "no-cache, no-store, must-revalidate"

# Invalidate CloudFront cache (if distribution ID is set)
if [[ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
    echo "Invalidating CloudFront distribution: $CLOUDFRONT_DISTRIBUTION_ID"
    aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"
else
    echo "Warning: CLOUDFRONT_DISTRIBUTION_ID not set, skipping CloudFront invalidation"
fi

echo "Dev deployment completed successfully!" 