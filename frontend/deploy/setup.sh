#!/bin/bash

# Create S3 bucket
aws s3api create-bucket \
    --bucket vogelring.com \
    --region eu-central-1 \
    --create-bucket-configuration LocationConstraint=eu-central-1

# Enable static website hosting
aws s3 website s3://vogelring.com/ --index-document index.html --error-document index.html

# Disable BlockPublicPolicy for the bucket
aws s3api put-public-access-block \
    --bucket vogelring.com \
    --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Apply bucket policy
aws s3api put-bucket-policy --bucket vogelring.com --policy file://deploy/bucket-policy.json

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://deploy/cloudfront-config.json
