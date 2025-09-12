# Frontend Migration Notes

## Changes Made for Local Backend Migration

### Environment Configuration
- **Removed AWS-specific environment variables**: `VITE_COGNITO_USER_POOL_ID`, `VITE_COGNITO_CLIENT_ID`, `VITE_API_KEY`, `S3_BUCKET`, `CLOUDFRONT_DISTRIBUTION_ID`
- **Updated API base URL**: Now points to local FastAPI backend at `http://localhost:8000`
- **Created new environment files**:
  - `.env.development`: `http://localhost:8000`
  - `.env.production`: `http://localhost:8000`
  - `.env.local`: `http://localhost:8000`

### Dependencies Removed
- `@aws-amplify/auth`
- `@aws-amplify/core`
- `@aws-sdk/client-cognito-identity-provider`
- `amazon-cognito-identity-js`

### Authentication Changes
- **Removed authentication system**: Authentication is now handled by Cloudflare Zero Trust
- **Simplified auth store**: Now always returns authenticated state
- **Removed authentication UI**: Login, register, and confirm signup pages deleted
- **Removed route guards**: All routes are now accessible (auth handled upstream)
- **Removed user menu**: No logout functionality needed

### API Client Changes
- **Removed JWT token handling**: No authentication headers sent to backend
- **Removed API key authentication**: Not needed for local backend
- **Simplified request/response interceptors**: Only logging remains
- **Updated health endpoint**: Changed from `/health` to `/` to match FastAPI backend

### Build Configuration
- **Removed AWS deployment scripts**: Only kept `dev`, `build`, and `preview` scripts
- **Updated version generation**: Added "local" suffix for local builds

### UI Changes
- **Removed authentication conditional rendering**: Search and navigation always visible
- **Removed user menu**: No user account management needed
- **Simplified navigation**: Direct access to all features

## Development Commands

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Docker Integration

The frontend will be served by nginx in the Docker Compose stack. The built files from `dist/` directory will be copied to the nginx container.

## API Endpoints

All API calls now go to the local FastAPI backend at `http://localhost:8000`. The API contract remains the same, but authentication headers are no longer sent.