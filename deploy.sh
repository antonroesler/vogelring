echo "Deploying API"

source .env
cd ring-api
sam build
sam deploy --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides RingApiKey=$RING_API_KEY

echo "Deploying frontend"
cd ../frontend
npm run deploy
