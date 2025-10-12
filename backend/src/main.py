"""
FastAPI main application entry point
"""

import logging
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .api.routers import (
    sightings,
    ringings,
    analytics,
    birds,
    places,
    species,
    dashboard,
    family,
    reports,
    suggestions,
    health,
    auth,
    admin,
)
from .database.connection import engine, get_db, create_tables, check_connection
from .database.models import Base
from .utils.logging_config import (
    setup_logging,
    get_log_level_from_env,
    get_log_file_from_env,
    setup_request_logging,
)
from .utils.version import get_package_version

# Setup logging configuration
setup_logging(log_level=get_log_level_from_env(), log_file=get_log_file_from_env())
logger = logging.getLogger("vogelring.main")

# Check if we're in development mode
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
if DEVELOPMENT_MODE:
    logger.info("Running in DEVELOPMENT MODE - authentication bypass enabled")

# Create database tables (only if not in test mode)
if not os.getenv("TESTING", False):
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

app = FastAPI(
    title="Vogelring API",
    description="Bird tracking and ringing management API",
    version=get_package_version(),
    docs_url="/swagger",
    redoc_url="/redoc",
)

# Store development mode in app state for access in routes
app.state.development_mode = DEVELOPMENT_MODE

# Configure CORS for frontend compatibility
# Note: Authentication is handled by Cloudflare Zero Trust before requests reach this application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "X-Requested-With"],
)

# Include routers with proper prefixes
app.include_router(sightings.router, prefix="/api", tags=["sightings"])
app.include_router(ringings.router, prefix="/api", tags=["ringings"])
app.include_router(birds.router, prefix="/api", tags=["birds"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(places.router, prefix="/api", tags=["places"])
app.include_router(species.router, prefix="/api", tags=["species"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(family.router, prefix="/api", tags=["family"])
app.include_router(reports.router, prefix="/api", tags=["reports"])
app.include_router(suggestions.router, prefix="/api", tags=["suggestions"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(health.router, tags=["health"])

# Setup request logging middleware
setup_request_logging(
    app, enable=os.getenv("ENABLE_REQUEST_LOGGING", "true").lower() == "true"
)

# Note: Health check endpoints are now handled by the health router


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Vogelring API", "version": get_package_version()}


@app.get("/api/")
async def api_root():
    """API root endpoint for frontend compatibility"""
    return {
        "message": "Vogelring API",
        "version": get_package_version(),
        "status": "running",
    }


# Cache invalidation endpoint (for compatibility)
@app.get("/api/cache/invalidate")
async def invalidate_cache():
    """Cache invalidation endpoint"""
    from .utils.cache import clear_cache

    try:
        clear_cache()
        logger.info("Cache invalidated successfully")
        return {"message": "Cache invalidated successfully"}
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        return {"message": f"Cache invalidation failed: {str(e)}"}
