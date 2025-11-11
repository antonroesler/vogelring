[![Lint API](https://github.com/antonroesler/vogelring/actions/workflows/ci.yml/badge.svg)](https://github.com/antonroesler/vogelring/actions/workflows/ci.yml)

# Vogelring 🦆

A comprehensive bird tracking and sighting management system for ornithologists and bird watchers. Vogelring enables researchers to track ringed birds, manage sightings, analyze migration patterns, and maintain detailed records of bird populations.

<img width="1308" alt="entrylist" src="https://github.com/user-attachments/assets/dd96a7c6-b3c9-45ba-a6bc-c33e816b36df" />
<img width="1308" alt="entry" src="https://github.com/user-attachments/assets/7a7501a6-ae95-4d1b-b405-5ffc54606c41" />
<img width="1308" alt="new" src="https://github.com/user-attachments/assets/2208b293-df06-4ab6-84e1-298cc546b293" />

## Features

### Core Functionality

- **Bird Sighting Management**: Record, edit, and track bird sightings with detailed metadata
- **Ring Database**: Comprehensive database of ringed birds with identification and tracking
- **Interactive Maps**: Visualize sightings on interactive maps with location accuracy indicators
- **Advanced Search**: Powerful search functionality with partial ring reading support (wildcards)
- **Family Trees**: Track breeding relationships and family lineages between birds

### Analytics & Insights

- **Friend Analysis**: Discover which birds are frequently seen together
- **Seasonal Patterns**: Analyze seasonal migration and behavior patterns
- **Dashboard**: Real-time statistics and insights about bird populations
- **Data Quality**: Built-in data validation and quality assessment tools
- **Radius Analysis**: Find all sightings within a specified geographic radius

### Data Management

- **Import/Export**: Support for various data formats and migration tools
- **Ringing Records**: Manage detailed ringing information and metadata
- **Reporting**: Generate shareable reports with customizable time ranges

## Getting Started

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

## Architecture

- **Frontend**: Vue.js 3 with TypeScript and Vuetify for Material Design components
- **Backend**: FastAPI application with PostgreSQL database
- **Infrastructure**: Docker Compose orchestration
- **Maps**: Leaflet for interactive mapping
- **Charts**: ECharts for data visualization

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
└── pyproject.toml
```

### Database Schema

The application uses PostgreSQL with three main tables:

- `ringings`: Bird ringing data
- `sightings`: Bird sighting observations
- `family_tree_entries`: Family relationship data

### Services

- **postgres**: PostgreSQL 15 database with persistent volumes
- **api**: FastAPI backend application
- **nginx**: Reverse proxy and static file server

## Data Model

### Core Entities

- **Sightings**: Individual bird observations with location, date, and metadata
- **Birds**: Unique ringed birds with identification and tracking information
- **Ringing**: Detailed ringing records including location, date, and ringer information
- **Family Trees**: Breeding relationships and lineage tracking

### Key Features

- **Flexible Data Entry**: Support for partial readings and uncertain identifications
- **Geographic Precision**: Exact and approximate location tracking
- **Temporal Analysis**: Date-based filtering and seasonal pattern analysis
- **Relationship Mapping**: Partner and offspring relationship tracking

## API Documentation

The API provides comprehensive endpoints for:

- **Sightings**: CRUD operations, filtering, and search
- **Birds**: Metadata retrieval and suggestions
- **Analytics**: Friend analysis, seasonal patterns, radius searches
- **Ringing**: Ringing record management
- **Family**: Family tree and relationship management

## Deployment

For production deployment:

1. **System requirements**:

   - Docker and Docker Compose installed
   - Sufficient storage for database and logs

2. **Configuration**:

   - Update `.env` with production values
   - Set up backup procedures for PostgreSQL data

3. **Monitoring**:
   - All services include health checks
   - Logs available via `docker-compose logs`

## Contact

For questions or to become a user, please contact: anton@antonroesler.com
