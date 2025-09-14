"""
Version utility functions
"""
import importlib.metadata
import logging

logger = logging.getLogger(__name__)

def get_package_version() -> str:
    """
    Get the version of the vogelring-backend package from metadata.
    
    Returns:
        str: The package version, or "unknown" if not found
    """
    try:
        return importlib.metadata.version("vogelring-backend")
    except importlib.metadata.PackageNotFoundError:
        logger.warning("Package version not found, falling back to unknown")
        return "unknown"
    except Exception as e:
        logger.error(f"Error getting package version: {e}")
        return "unknown"