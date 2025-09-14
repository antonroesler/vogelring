"""
Configuration for migration scripts
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
DYNAMO_TABLE_NAME = os.getenv("DYNAMO_TABLE_NAME", "vogelring")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_SIGHTINGS_FILE = os.getenv("S3_SIGHTINGS_FILE", "sightings.pkl")

# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "vogelring")
POSTGRES_USER = os.getenv("POSTGRES_USER", "vogelring")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Build PostgreSQL connection URL
if POSTGRES_PASSWORD:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    DATABASE_URL = f"postgresql://{POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Migration Configuration
BATCH_SIZE = 1000  # Number of records to process in each batch
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
VALIDATE_DATA = os.getenv("VALIDATE_DATA", "true").lower() == "true"

# Family Tree suffix used in DynamoDB
FAMILY_TREE_SUFFIX = "#FT"

# User context (for single-user migration)
DEFAULT_USER = os.getenv("DEFAULT_USER", "default")