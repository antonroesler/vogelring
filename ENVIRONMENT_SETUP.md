# Quick Dev Environment Setup Guide

## 1. Create Environment Files

```bash
# Copy the example files
cp .env.dev.example .env.dev
cp .env.prod.example .env.prod
```

## 2. Configure Development Environment

Edit `.env.dev` with your development settings:

```bash
# Required: Your API key for development
RING_API_KEY=your-dev-api-key-here

# AWS Resources (these will be created automatically)
S3_BUCKET=vogelring-data-dev
DYNAMO_TABLE=vogelring-dev
CLOUDFRONT_DOMAIN=dev.vogelring.com

# Frontend URLs (update after first deployment)
VITE_API_URL=https://your-dev-api-url.execute-api.eu-central-1.amazonaws.com/Prod
VITE_API_KEY=your-dev-api-key-here
```

## 3. Create AWS Resources for Dev

The following resources need to be created in AWS for your dev environment:

1. **S3 Bucket**: `vogelring-data-dev`
2. **DynamoDB Table**: `vogelring-dev` (with same schema as prod)

You can create these manually or they'll be referenced by your Lambda functions.

## 4. Deploy to Development

```bash
./deploy.sh dev
```

This will:

- Deploy the API stack as `ring-api-dev`
- Deploy the frontend to your dev S3 bucket
- Output the API Gateway URL for your frontend configuration

## 5. Update Frontend Configuration

After the first deployment, update `.env.dev` with the actual API Gateway URL from the deployment output.

## 6. Test Your Setup

```bash
# Test local development
./run.sh dev

# Test dev deployment
./deploy.sh dev
```

## 7. Normal Development Workflow

1. Make changes to your code
2. Test locally: `./run.sh dev`
3. Deploy to dev: `./deploy.sh dev`
4. Test in dev environment
5. When ready, deploy to prod: `./deploy.sh prod`

## Troubleshooting

- **Missing .env file**: Make sure you created `.env.dev` from the example
- **AWS permissions**: Ensure your AWS CLI has proper permissions
- **Stack conflicts**: Check that you're using the correct environment names
