#!/bin/bash

# Build the project
npm run build

# Sync the dist folder with the S3 bucket
aws s3 sync dist/ s3://vogelring.com

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_CLOUDFRONT_DISTRIBUTION_ID --paths "/*" 