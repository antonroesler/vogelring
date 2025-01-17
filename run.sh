#!/bin/bash
echo "Running Frontend"

source .env
export VITE_API_KEY=$RING_API_KEY

cd frontend
npm run dev