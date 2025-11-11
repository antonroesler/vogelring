"""
Health check endpoints for monitoring service availability
"""

import logging
import psutil
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ...database.connection import get_db, check_connection
from ...utils.cache import get_cache_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint
    Returns simple status for load balancer health checks
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "vogelring-backend",
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with database and system information
    """
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "vogelring-backend",
        "checks": {},
    }

    # Database connectivity check
    try:
        db_healthy = check_connection()
        health_data["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection successful"
            if db_healthy
            else "Database connection failed",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}",
        }
        health_data["status"] = "unhealthy"

    # Cache statistics
    try:
        cache_stats = get_cache_stats()
        health_data["checks"]["cache"] = {"status": "healthy", "stats": cache_stats}
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_data["checks"]["cache"] = {
            "status": "unhealthy",
            "message": f"Cache error: {str(e)}",
        }

    # System resource check (Raspberry Pi specific)
    try:
        system_stats = get_system_stats()
        health_data["checks"]["system"] = {"status": "healthy", "stats": system_stats}

        # Check for resource warnings
        if system_stats["memory_percent"] > 85:
            health_data["checks"]["system"]["warnings"] = ["High memory usage"]
        if system_stats["cpu_percent"] > 80:
            health_data["checks"]["system"]["warnings"] = health_data["checks"][
                "system"
            ].get("warnings", []) + ["High CPU usage"]
        if system_stats["disk_percent"] > 90:
            health_data["checks"]["system"]["warnings"] = health_data["checks"][
                "system"
            ].get("warnings", []) + ["High disk usage"]

    except Exception as e:
        logger.error(f"System health check failed: {e}")
        health_data["checks"]["system"] = {
            "status": "unhealthy",
            "message": f"System monitoring error: {str(e)}",
        }

    return health_data


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/Docker health checks
    Returns 200 if service is ready to accept traffic
    """
    try:
        # Check database connectivity
        if not check_connection():
            raise HTTPException(status_code=503, detail="Database not ready")

        # Check if we can perform a simple query
        db.execute(text("SELECT 1"))

        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes/Docker health checks
    Returns 200 if service is alive (doesn't check dependencies)
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


def get_system_stats() -> Dict[str, Any]:
    """
    Get system resource statistics optimized for Raspberry Pi monitoring
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage for root partition
        disk = psutil.disk_usage("/")

        # System load
        load_avg = psutil.getloadavg()

        # Temperature (Raspberry Pi specific)
        temperature = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_raw = int(f.read().strip())
                temperature = temp_raw / 1000.0  # Convert from millidegrees
        except (FileNotFoundError, ValueError, PermissionError):
            # Not on Raspberry Pi or no permission
            pass

        stats = {
            "cpu_percent": round(cpu_percent, 2),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": round(memory.percent, 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 2),
            "load_average": {
                "1min": round(load_avg[0], 2),
                "5min": round(load_avg[1], 2),
                "15min": round(load_avg[2], 2),
            },
        }

        if temperature is not None:
            stats["temperature_celsius"] = round(temperature, 1)

        return stats

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return {"error": str(e)}
