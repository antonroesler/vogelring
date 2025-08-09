#!/bin/bash

# Build the project with prod environment variables  
npm run build -- --mode production


bash deploy/deploy.sh