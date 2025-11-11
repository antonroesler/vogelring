"""
Logging configuration for the Vogelring backend application
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Setup logging configuration for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs only to console
    """

    # Create logs directory if logging to file
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # Define log format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    detailed_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s"

    # Base logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": log_format, "datefmt": "%Y-%m-%d %H:%M:%S"},
            "detailed": {"format": detailed_format, "datefmt": "%Y-%m-%d %H:%M:%S"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": sys.stdout,
            }
        },
        "loggers": {
            # Application loggers
            "vogelring": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            # Database loggers
            "sqlalchemy.engine": {
                "level": "WARNING",  # Reduce SQL query noise unless debugging
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            # FastAPI/Uvicorn loggers
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {"level": "INFO", "handlers": ["console"], "propagate": False},
        },
        "root": {"level": log_level, "handlers": ["console"]},
    }

    # Add file handler if log file specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        }

        # Add file handler to all loggers
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("file")
        config["root"]["handlers"].append("file")

    # Apply configuration
    logging.config.dictConfig(config)

    # Log startup message
    logger = logging.getLogger("vogelring.startup")
    logger.info(
        f"Logging configured - Level: {log_level}, File: {log_file or 'Console only'}"
    )


def get_log_level_from_env() -> str:
    """Get log level from environment variable with fallback"""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_log_file_from_env() -> str:
    """Get log file path from environment variable"""
    log_file = os.getenv("LOG_FILE")
    if log_file:
        # Expand relative paths
        if not os.path.isabs(log_file):
            log_file = os.path.join(os.getcwd(), log_file)
    return log_file


class RequestLoggingMiddleware:
    """
    Middleware to log HTTP requests and responses
    """

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("vogelring.requests")

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = datetime.now()

            # Log request
            method = scope["method"]
            path = scope["path"]
            query_string = scope.get("query_string", b"").decode()
            client_ip = scope.get("client", ["unknown", None])[0]

            self.logger.info(
                f"Request: {method} {path}?{query_string} from {client_ip}"
            )

            # Capture response
            status_code = None

            async def send_wrapper(message):
                nonlocal status_code
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                await send(message)

            await self.app(scope, receive, send_wrapper)

            # Log response
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(
                f"Response: {status_code} for {method} {path} in {duration:.3f}s"
            )
        else:
            await self.app(scope, receive, send)


def setup_request_logging(app, enable: bool = True):
    """
    Add request logging middleware to FastAPI app

    Args:
        app: FastAPI application instance
        enable: Whether to enable request logging
    """
    if enable and not os.getenv("TESTING", False):
        app.add_middleware(RequestLoggingMiddleware)
        logger = logging.getLogger("vogelring.startup")
        logger.info("Request logging middleware enabled")
