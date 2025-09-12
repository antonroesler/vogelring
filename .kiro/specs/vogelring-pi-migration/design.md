# Design Document

## Overview

This design document outlines the migration of the Vogelring bird tracking application from AWS serverless architecture to a self-hosted solution on Raspberry Pi 5. The migration transforms AWS Lambda functions into a FastAPI application, replaces DynamoDB and S3 pickle storage with PostgreSQL, and containerizes the entire stack using Docker Compose.

The key architectural change is moving from a serverless, multi-service AWS setup to a monolithic containerized application optimized for single-user operation on edge hardware.

## Architecture

### Current Architecture (AWS)
- **Frontend**: Vue.js SPA served from S3 + CloudFront
- **Backend**: Two AWS Lambda functions (reader/writer) with API Gateway
- **Data Storage**: DynamoDB for ringings (~6K records) + S3 pickle files for sightings (~8K records)
- **Authentication**: AWS Cognito with JWT tokens
- **Infrastructure**: AWS SAM for deployment

### Target Architecture (Raspberry Pi)
- **Frontend**: Vue.js SPA served via nginx container
- **Backend**: FastAPI application in Python container
- **Database**: PostgreSQL container with persistent volumes
- **Reverse Proxy**: nginx for routing and static file serving
- **Authentication**: Removed (handled by Cloudflare Zero Trust)
- **Infrastructure**: Docker Compose for orchestration

### Architecture Diagram

```mermaid
graph TB
    subgraph "Cloudflare Zero Trust"
        CF[Cloudflare Tunnel]
    end
    
    subgraph "Raspberry Pi 5"
        subgraph "Docker Compose Stack"
            NGINX[nginx<br/>Reverse Proxy]
            API[FastAPI<br/>Backend]
            DB[(PostgreSQL<br/>Database)]
            FRONTEND[Static Files<br/>Vue.js SPA]
        end
    end
    
    CF --> NGINX
    NGINX --> API
    NGINX --> FRONTEND
    API --> DB
    
    style CF fill:#f9f,stroke:#333,stroke-width:2px
    style NGINX fill:#e1f5fe,stroke:#333,stroke-width:2px
    style API fill:#f3e5f5,stroke:#333,stroke-width:2px
    style DB fill:#e8f5e8,stroke:#333,stroke-width:2px
```

## Components and Interfaces

### 1. FastAPI Backend Service

**Purpose**: Replace AWS Lambda functions with a single FastAPI application

**Key Components**:
- **Router Layer**: FastAPI routers for different endpoint groups (sightings, ringings, analytics)
- **Service Layer**: Business logic layer (preserved from current implementation)
- **Database Layer**: SQLAlchemy ORM for PostgreSQL operations
- **Models Layer**: Pydantic models (preserved from current implementation)

**Interface Changes**:
- Remove AWS Lambda Powertools dependencies
- Remove Cognito authentication middleware
- Remove user context filtering (single-user application)
- Add SQLAlchemy database session management
- Add FastAPI dependency injection for database connections

### 2. PostgreSQL Database

**Purpose**: Replace DynamoDB + S3 pickle files with unified relational storage

**Schema Design**:

```sql
-- Ringings table (migrated from DynamoDB)
CREATE TABLE ringings (
    id UUID PRIMARY KEY,
    ring VARCHAR(50) UNIQUE NOT NULL,
    ring_scheme VARCHAR(50) NOT NULL,
    species VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    place VARCHAR(200) NOT NULL,
    lat DECIMAL(9, 6) NOT NULL,  -- Latitude: -90.123456 to 90.123456 (~10cm precision)
    lon DECIMAL(10, 6) NOT NULL, -- Longitude: -180.123456 to 180.123456 (~10cm precision)
    ringer VARCHAR(100) NOT NULL,
    sex INTEGER NOT NULL,
    age INTEGER NOT NULL,
    status VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sightings table (migrated from pickle files)
CREATE TABLE sightings (
    id UUID PRIMARY KEY,
    excel_id INTEGER,
    comment TEXT,
    species VARCHAR(100),
    ring VARCHAR(50),
    reading VARCHAR(50),
    age VARCHAR(10),
    sex CHAR(1),
    date DATE,
    large_group_size INTEGER,
    small_group_size INTEGER,
    partner VARCHAR(50),
    breed_size INTEGER,
    family_size INTEGER,
    pair VARCHAR(10),
    status VARCHAR(10),
    melder VARCHAR(100),
    melded BOOLEAN,
    place VARCHAR(200),
    area VARCHAR(200),
    lat DECIMAL(9, 6),  -- Latitude with ~10cm precision
    lon DECIMAL(10, 6), -- Longitude with ~10cm precision
    is_exact_location BOOLEAN DEFAULT FALSE,
    habitat VARCHAR(100),
    field_fruit VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Family tree entries (migrated from DynamoDB)
CREATE TABLE family_tree_entries (
    id UUID PRIMARY KEY,
    ring VARCHAR(50) UNIQUE NOT NULL,
    partners JSONB,
    children JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_sightings_ring ON sightings(ring);
CREATE INDEX idx_sightings_species ON sightings(species);
CREATE INDEX idx_sightings_place ON sightings(place);
CREATE INDEX idx_sightings_date ON sightings(date);
CREATE INDEX idx_sightings_reading ON sightings(reading);
CREATE INDEX idx_ringings_ring ON ringings(ring);
CREATE INDEX idx_ringings_species ON ringings(species);
```

### 3. Data Access Layer

**Purpose**: Provide efficient database operations with SQLAlchemy ORM

**Key Components**:
- **Models**: SQLAlchemy ORM models matching the Pydantic schemas
- **Repositories**: Data access patterns for each entity type
- **Query Builders**: Optimized queries for autocomplete and filtering
- **Connection Management**: Database connection pooling and session management

**Enhanced Sighting Queries**:
```python
# Example: Enriched sighting query with ringing data
def get_enriched_sightings() -> List[EnrichedSighting]:
    return session.query(Sighting)\
        .outerjoin(Ringing, Sighting.ring == Ringing.ring)\
        .options(contains_eager(Sighting.ringing_data))\
        .all()
```

### 4. Docker Compose Stack

**Purpose**: Orchestrate all services with proper networking and persistence

**Services Configuration**:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: vogelring
      POSTGRES_USER: vogelring
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  api:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://vogelring:${DB_PASSWORD}@postgres:5432/vogelring
    depends_on:
      - postgres
    ports:
      - "8000:8000"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    volumes:
      - ./frontend/dist:/usr/share/nginx/html
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
```

### 5. Migration Tools

**Purpose**: Transfer existing AWS data to local PostgreSQL

**Components**:
- **DynamoDB Exporter**: Script to export ringing and family tree data
- **S3 Pickle Converter**: Script to convert pickle files to database records
- **Data Validator**: Verify data integrity after migration
- **Backup/Restore**: Database backup utilities

## Data Models

### Enhanced Sighting Model

The sighting model will be enhanced to include ringing data when available:

```python
class EnrichedSighting(Sighting):
    """Sighting with optional ringing data merged at application level"""
    ringing_data: Optional[Ringing] = None
    
    @classmethod
    def from_sighting_and_ringing(cls, sighting: Sighting, ringing: Optional[Ringing]):
        data = sighting.model_dump()
        data['ringing_data'] = ringing
        return cls(**data)
```

### Database Models

SQLAlchemy models will mirror the Pydantic models:

```python
class SightingDB(Base):
    __tablename__ = "sightings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ring = Column(String(50), index=True)
    species = Column(String(100), index=True)
    # ... other fields
    
    # Relationship to ringing data
    ringing_data = relationship("RingingDB", foreign_keys=[ring], 
                               primaryjoin="SightingDB.ring == RingingDB.ring")
```

## Error Handling

### Database Connection Management
- **Connection Pooling**: Use SQLAlchemy connection pooling for efficient resource usage
- **Retry Logic**: Implement retry mechanisms for transient database errors
- **Health Checks**: Database connectivity health checks for Docker Compose

### Data Validation
- **Pydantic Validation**: Maintain existing Pydantic model validation
- **Database Constraints**: Add database-level constraints for data integrity
- **Migration Validation**: Verify data consistency during migration

### API Error Responses
- **FastAPI Exception Handlers**: Replace Lambda Powertools error handling
- **Structured Error Responses**: Maintain consistent error response format
- **Logging**: Structured logging with correlation IDs

## Testing Strategy

### Unit Tests
- **Service Layer Tests**: Test business logic with mocked database
- **Repository Tests**: Test database operations with test database
- **Model Tests**: Test Pydantic model validation and serialization

### Integration Tests
- **API Endpoint Tests**: Test complete request/response cycles
- **Database Integration**: Test with real PostgreSQL test instance
- **Docker Compose Tests**: Test full stack deployment

### Migration Tests
- **Data Integrity Tests**: Verify migrated data matches source
- **Performance Tests**: Ensure query performance meets requirements
- **Rollback Tests**: Test migration rollback procedures

### Test Structure
```
tests/
├── unit/
│   ├── test_services.py
│   ├── test_models.py
│   └── test_repositories.py
├── integration/
│   ├── test_api.py
│   ├── test_database.py
│   └── test_migration.py
└── fixtures/
    ├── sample_data.py
    └── test_database.py
```

## Performance Considerations

### Database Optimization
- **Indexing Strategy**: Indexes on frequently queried columns (ring, species, place, date)
- **Query Optimization**: Use JOINs instead of separate queries for ringing data
- **Connection Pooling**: Optimize for Raspberry Pi memory constraints

### Caching Strategy
- **Application-Level Caching**: Cache frequently accessed data (species lists, place names)
- **Query Result Caching**: Cache expensive analytical queries
- **Memory Management**: Optimize for 8GB Raspberry Pi RAM

### Resource Constraints
- **Container Resource Limits**: Set appropriate CPU and memory limits
- **Database Tuning**: PostgreSQL configuration optimized for Raspberry Pi
- **Monitoring**: Basic resource monitoring and alerting

## Security Considerations

### Authentication Removal
- **No Internal Auth**: Remove all Cognito and JWT handling
- **Cloudflare Zero Trust**: Rely on external authentication layer
- **API Security**: Remove API key validation (handled upstream)

### Data Security
- **Database Encryption**: Use encrypted volumes for sensitive data
- **Network Security**: Internal Docker network isolation
- **Backup Security**: Encrypted database backups

### Container Security
- **Minimal Images**: Use Alpine-based images for smaller attack surface
- **Non-Root Users**: Run containers with non-root users
- **Security Updates**: Regular base image updates

## Deployment and Operations

### Deployment Process
1. **Build Images**: Build FastAPI and nginx containers
2. **Database Setup**: Initialize PostgreSQL with schema
3. **Data Migration**: Run migration scripts for existing data
4. **Service Startup**: Start Docker Compose stack
5. **Health Verification**: Verify all services are healthy

### Monitoring and Logging
- **Centralized Logging**: Docker Compose logging configuration
- **Health Checks**: Docker health checks for all services
- **Basic Monitoring**: Resource usage monitoring
- **Alerting**: Simple alerting for service failures

### Backup and Recovery
- **Database Backups**: Automated PostgreSQL backups
- **Volume Backups**: Docker volume backup procedures
- **Recovery Testing**: Regular recovery procedure testing
- **Documentation**: Clear recovery procedures

### Maintenance Procedures
- **Updates**: Container image update procedures
- **Scaling**: Vertical scaling considerations for Raspberry Pi
- **Troubleshooting**: Common issue resolution guides
- **Performance Tuning**: Optimization procedures for edge hardware