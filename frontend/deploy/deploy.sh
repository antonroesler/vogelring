#!/bin/bash


echo "Deploying Frontend to $ENVIRONMENT environment..."
echo "S3 Bucket: $S3_BUCKET"
echo "CloudFront Distribution ID: $CLOUDFRONT_DISTRIBUTION_ID"

# Sync the dist folder with the prod S3 bucket
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

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $CLOUDFRONT_DISTRIBUTION_ID --paths "/*"

echo "Deployment completed successfully!" 