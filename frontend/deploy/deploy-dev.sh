#!/bin/bash

# Development frontend deployment script


# Build the project with dev environment variables
npm run build -- --mode development

bash deploy/deploy.sh