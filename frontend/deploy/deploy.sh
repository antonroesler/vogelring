#!/bin/bash

# Source the API key from root .env file
export VITE_API_KEY=$RING_API_KEY

echo "VITE_API_KEY=$VITE_API_KEY"

# Build the project
npm run build

# Sync the dist folder with the S3 bucket
aws s3 sync dist/ s3://vogelring.com

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id E1JFMT0RGVCMKH --paths "/*" 