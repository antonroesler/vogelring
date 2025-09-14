# Vogelring - Bird Tracking Application

A bird tracking and ringing management application migrated from AWS serverless architecture to a self-hosted solution running on Raspberry Pi 5.

## Architecture

- **Frontend**: Vue.js SPA served via nginx
- **Backend**: FastAPI application with PostgreSQL database
- **Infrastructure**: Docker Compose orchestration
- **Authentication**: Handled by Cloudflare Zero Trust (external)

## Quick Start

1. **Clone and setup environment**:
   ```bash
   git clone <repository>
   cd vogelring
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Build and start services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost
   - API: http://localhost/api
   - Health check: http://localhost/health

## Development

### Backend Development

The FastAPI backend is located in the `backend/` directory:

```
backend/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── database/
│   │   ├── connection.py    # Database connection and session management
│   │   └── models.py        # SQLAlchemy ORM models
│   └── api/
│       └── routers/         # API route handlers
├── Dockerfile
└── requirements.txt
```

### Database Schema

The application uses PostgreSQL with three main tables:
- `ringings`: Bird ringing data (~6K records)
- `sightings`: Bird sighting observations (~8K records)  
- `family_tree_entries`: Family relationship data

### Services

- **postgres**: PostgreSQL 15 database with persistent volumes
- **api**: FastAPI backend application
- **nginx**: Reverse proxy and static file server

## Deployment

For production deployment on Raspberry Pi:

1. **System requirements**:
   - Raspberry Pi 5 with 8GB RAM
   - Docker and Docker Compose installed
   - Sufficient storage for database and logs

2. **Configuration**:
   - Update `.env` with production values
   - Configure Cloudflare tunnel for external access
   - Set up backup procedures for PostgreSQL data

3. **Monitoring**:
   - All services include health checks
   - Logs available via `docker-compose logs`
   - Resource monitoring recommended for Pi hardware

## Migration from AWS

This application was migrated from AWS Lambda + DynamoDB + S3 to a containerized stack. Key changes:

- AWS Lambda → FastAPI application
- DynamoDB + S3 pickle files → PostgreSQL database
- AWS Cognito → Cloudflare Zero Trust authentication
- Multi-user → Single-user operation

Migration scripts for existing data will be provided in subsequent tasks.