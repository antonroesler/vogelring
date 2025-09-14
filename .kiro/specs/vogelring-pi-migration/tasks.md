# Implementation Plan

- [x] 1. Set up project structure and database foundation
  - Create new backend directory structure for FastAPI application
  - Set up PostgreSQL database schema with tables for sightings, ringings, and family_tree_entries
  - Create Docker Compose configuration with PostgreSQL, FastAPI, and nginx services
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 2. Implement database models and connection layer
  - [x] 2.1 Create SQLAlchemy database models
    - Write SQLAlchemy ORM models for Sighting, Ringing, and FamilyTreeEntry tables
    - Add proper relationships, indexes, and constraints
    - Create database connection and session management utilities
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

  - [x] 2.2 Implement database repository layer
    - Create repository classes for data access operations (SightingRepository, RingingRepository)
    - Implement CRUD operations with SQLAlchemy queries
    - Add optimized queries for autocomplete and filtering functionality
    - _Requirements: 2.3, 2.4, 7.1, 7.2_

- [x] 3. Create FastAPI application structure
  - [x] 3.1 Set up FastAPI application and routing
    - Create main FastAPI application with dependency injection for database sessions
    - Set up router modules for sightings, ringings, analytics, and other endpoint groups
    - Configure CORS settings for frontend compatibility
    - _Requirements: 1.1, 1.5, 5.3_

  - [x] 3.2 Remove authentication and user context handling
    - Strip out all Cognito authentication middleware and JWT token handling
    - Remove user context parameters from all service functions and API endpoints
    - Simplify request handling without user filtering
    - _Requirements: 1.3, 1.4_

- [x] 4. Migrate service layer to work with PostgreSQL
  - [x] 4.1 Update sighting services for database operations
    - Modify get_sightings, add_sighting, update_sighting, delete_sighting to use PostgreSQL repositories
    - Implement enriched sighting queries that JOIN with ringing data
    - Update sighting filtering and search functionality for database queries
    - _Requirements: 2.3, 2.6, 7.3_

  - [x] 4.2 Update ringing services for database operations
    - Modify get_ringing_by_ring, upsert_ringing, delete_ringing to use PostgreSQL repositories
    - Remove DynamoDB client dependencies and replace with SQLAlchemy operations
    - _Requirements: 2.1, 2.4_

  - [x] 4.3 Update analytics and suggestion services
    - Modify analytics functions (friends analysis, seasonal analysis) to use SQL queries
    - Update suggestion services (species lists, place names) to query database efficiently
    - Implement caching for frequently accessed suggestion data
    - _Requirements: 2.3, 7.4_

- [x] 5. Create data migration scripts
  - [x] 5.1 Implement DynamoDB to PostgreSQL migration
    - Write script to export ringing data from DynamoDB and insert into PostgreSQL
    - Write script to export family tree entries from DynamoDB and insert into PostgreSQL
    - Add data validation and integrity checks during migration
    - _Requirements: 4.1, 4.3, 4.4_

  - [x] 5.2 Implement S3 pickle to PostgreSQL migration
    - Write script to load sighting data from S3 pickle files and insert into PostgreSQL
    - Handle data type conversions and validation during migration
    - Preserve all existing sighting metadata and relationships
    - _Requirements: 4.2, 4.3, 4.4_

- [x] 6. Set up Docker containerization
  - [x] 6.1 Create FastAPI application Dockerfile
    - Write Dockerfile for FastAPI backend with Python dependencies
    - Configure container to run FastAPI with uvicorn server
    - Set up proper environment variable handling and health checks
    - _Requirements: 3.1, 3.3_

  - [x] 6.2 Configure nginx for frontend and reverse proxy
    - Create nginx configuration to serve Vue.js frontend static files
    - Set up reverse proxy rules to route API requests to FastAPI backend
    - Configure proper CORS headers and static file caching
    - _Requirements: 3.1, 5.1, 5.4_

  - [x] 6.3 Complete Docker Compose configuration
    - Finalize docker-compose.yml with all services, networking, and volume configurations
    - Add environment file templates and configuration management
    - Set up proper service dependencies and restart policies
    - _Requirements: 3.2, 3.4, 8.1_

- [x] 7. Update frontend configuration for local backend
  - [x] 7.1 Update API configuration and build process
    - Modify frontend environment variables to point to local FastAPI backend
    - Update API client configuration to work with new backend URL structure
    - Remove any AWS-specific frontend configuration and authentication handling
    - _Requirements: 5.1, 5.2, 5.5_

- [x] 8. Implement basic testing suite
  - [x] 8.1 Create API endpoint tests
    - Write pytest tests for core CRUD operations on sightings and ringings endpoints
    - Test analytics endpoints and suggestion/autocomplete functionality
    - Create test fixtures with sample data for consistent testing
    - _Requirements: 6.1, 6.2_

  - [x] 8.2 Create database integration tests
    - Write tests for database repository operations and data integrity
    - Test migration scripts with sample data validation
    - Create database setup and teardown utilities for testing
    - _Requirements: 6.3, 6.4_

- [x] 9. Add performance optimizations and monitoring
  - [x] 9.1 Implement database performance optimizations
    - Add database indexes for frequently queried columns (ring, species, place, date)
    - Implement connection pooling configuration optimized for Raspberry Pi resources
    - Add query optimization for autocomplete and filtering operations
    - _Requirements: 7.1, 7.2, 7.5_

  - [x] 9.2 Add basic monitoring and health checks
    - Implement health check endpoints for all services in Docker Compose
    - Add basic logging configuration for FastAPI application and database operations
    - Create simple monitoring for resource usage and service availability
    - _Requirements: 8.2, 8.3_

- [-] 10. Create deployment and operational documentation
  - [ ] 10.1 Write deployment procedures and scripts
    - Create deployment scripts for initial setup and updates
    - Document environment setup and configuration procedures
    - Write backup and restore procedures for PostgreSQL database
    - _Requirements: 8.1, 8.4_

- [x] 11. Frontend build and configuration finalization
  - [x] 11.1 Build frontend for production
    - Run frontend build process to generate optimized static files
    - Ensure all frontend dependencies are properly configured
    - Verify frontend API configuration points to correct backend endpoints
    - _Requirements: 5.1, 5.2, 5.4_

- [x] 12. End-to-end system validation
  - [x] 12.1 Run complete system locally
    - Start all services with Docker Compose and verify connectivity
    - Test frontend-to-backend communication and database operations
    - Validate that all major user workflows function correctly
    - _Requirements: 6.1, 6.2, 8.2_ 