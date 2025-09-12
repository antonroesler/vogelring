#!/usr/bin/env python3
"""
S3 Pickle to PostgreSQL Migration Script

This script migrates sighting data from S3 pickle files to PostgreSQL.
It handles data validation, batch processing, and integrity checks.

Usage:
    python migrate_s3_pickle.py [--dry-run] [--validate-only] [--truncate] [--user USER]

Environment Variables:
    AWS_REGION: AWS region for S3 (default: eu-central-1)
    S3_BUCKET_NAME: S3 bucket name (required)
    S3_SIGHTINGS_FILE: S3 sightings file name (default: sightings.pkl)
    POSTGRES_HOST: PostgreSQL host (default: localhost)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_DB: PostgreSQL database name (default: vogelring)
    POSTGRES_USER: PostgreSQL username (default: vogelring)
    POSTGRES_PASSWORD: PostgreSQL password (required)
    DEFAULT_USER: Default user for single-user migration (default: default)
    DRY_RUN: Set to 'true' for dry run mode (default: false)
    VALIDATE_DATA: Set to 'true' to validate data after migration (default: true)
"""

import logging
import sys
import argparse
import pickle
from typing import List, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json

from config import (
    AWS_REGION, S3_BUCKET_NAME, S3_SIGHTINGS_FILE, BATCH_SIZE, 
    DRY_RUN, VALIDATE_DATA, DEFAULT_USER
)
from models import Sighting
from database import (
    create_tables, test_connection, get_db_session, get_table_count,
    truncate_table, validate_data_integrity, SightingDB
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_s3_pickle.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class S3PickleMigrator:
    """Handles migration from S3 pickle files to PostgreSQL"""
    
    def __init__(self, dry_run: bool = False, user: str = DEFAULT_USER):
        self.dry_run = dry_run
        self.user = user
        self.s3_client = None
        self.stats = {
            'sightings_processed': 0,
            'sightings_migrated': 0,
            'sightings_skipped': 0,
            'errors': 0
        }
    
    def connect_s3(self) -> bool:
        """Connect to S3"""
        try:
            self.s3_client = boto3.client('s3', region_name=AWS_REGION)
            
            # Test connection by listing bucket
            self.s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            logger.info(f"Connected to S3 bucket: {S3_BUCKET_NAME}")
            return True
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            return False
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket {S3_BUCKET_NAME} not found")
            else:
                logger.error(f"Error connecting to S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to S3: {e}")
            return False
    
    def get_user_sighting_file_key(self) -> str:
        """Get the S3 key for the user's sighting file"""
        if self.user == "":
            return S3_SIGHTINGS_FILE  # Root level file
        return f"{self.user}/{S3_SIGHTINGS_FILE}"
    
    def load_sightings_from_s3(self) -> Optional[List[Any]]:
        """Load sighting data from S3 pickle file"""
        s3_key = self.get_user_sighting_file_key()
        
        try:
            logger.info(f"Loading sightings from S3: {S3_BUCKET_NAME}/{s3_key}")
            
            # Get object from S3
            response = self.s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            
            # Load pickle data
            pickle_data = pickle.loads(response['Body'].read())
            
            logger.info(f"Loaded {len(pickle_data)} sighting records from S3")
            return pickle_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"S3 object {s3_key} not found in bucket {S3_BUCKET_NAME}")
            else:
                logger.error(f"Error loading from S3: {e}")
            return None
        except pickle.PickleError as e:
            logger.error(f"Error unpickling data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading from S3: {e}")
            return None
    
    def convert_pickle_item_to_sighting(self, item: Any) -> Optional[Sighting]:
        """Convert pickle item to Sighting model"""
        try:
            # Handle different possible formats of pickle data
            if isinstance(item, dict):
                # If it's already a dictionary, use it directly
                sighting_data = item
            elif hasattr(item, 'model_dump'):
                # If it's a Pydantic model, convert to dict
                sighting_data = item.model_dump()
            elif hasattr(item, '__dict__'):
                # If it's an object with attributes, convert to dict
                sighting_data = item.__dict__
            else:
                logger.error(f"Unknown pickle item format: {type(item)}")
                return None
            
            # Handle date conversion if needed
            if 'date' in sighting_data and isinstance(sighting_data['date'], str):
                try:
                    sighting_data['date'] = datetime.fromisoformat(sighting_data['date']).date()
                except ValueError:
                    # Try other date formats if needed
                    logger.warning(f"Could not parse date: {sighting_data['date']}")
                    sighting_data['date'] = None
            
            # Create Sighting model with validation
            return Sighting(**sighting_data)
            
        except Exception as e:
            logger.error(f"Error converting pickle item to Sighting: {e}")
            logger.error(f"Item data: {json.dumps(item, default=str)}")
            return None
    
    def migrate_sightings(self, sightings_data: List[Any]) -> int:
        """Migrate sighting records to PostgreSQL"""
        migrated_count = 0
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {len(sightings_data)} sighting records")
            return len(sightings_data)
        
        try:
            with get_db_session() as session:
                for i, item in enumerate(sightings_data):
                    self.stats['sightings_processed'] += 1
                    
                    # Convert pickle item to Pydantic model
                    sighting = self.convert_pickle_item_to_sighting(item)
                    if not sighting:
                        self.stats['errors'] += 1
                        continue
                    
                    # Check if record already exists (by excel_id if available, otherwise by unique combination)
                    existing = None
                    if sighting.excel_id:
                        existing = session.query(SightingDB).filter_by(excel_id=sighting.excel_id).first()
                    
                    # If no excel_id or not found by excel_id, check by other unique fields
                    if not existing and sighting.ring and sighting.date:
                        existing = session.query(SightingDB).filter_by(
                            ring=sighting.ring,
                            date=sighting.date,
                            place=sighting.place
                        ).first()
                    
                    if existing:
                        logger.debug(f"Sighting already exists (excel_id: {sighting.excel_id}, ring: {sighting.ring}), skipping")
                        self.stats['sightings_skipped'] += 1
                        continue
                    
                    # Create database record
                    db_sighting = SightingDB(
                        excel_id=sighting.excel_id,
                        comment=sighting.comment,
                        species=sighting.species,
                        ring=sighting.ring,
                        reading=sighting.reading,
                        age=sighting.age.value if sighting.age else None,
                        sex=sighting.sex,
                        date=sighting.date,
                        large_group_size=sighting.large_group_size,
                        small_group_size=sighting.small_group_size,
                        partner=sighting.partner,
                        breed_size=sighting.breed_size,
                        family_size=sighting.family_size,
                        pair=sighting.pair.value if sighting.pair else None,
                        status=sighting.status.value if sighting.status else None,
                        melder=sighting.melder,
                        melded=sighting.melded,
                        place=sighting.place,
                        area=sighting.area,
                        lat=sighting.lat,
                        lon=sighting.lon,
                        is_exact_location=sighting.is_exact_location,
                        habitat=sighting.habitat,
                        field_fruit=sighting.field_fruit
                    )
                    
                    session.add(db_sighting)
                    migrated_count += 1
                    self.stats['sightings_migrated'] += 1
                    
                    # Commit in batches
                    if (i + 1) % BATCH_SIZE == 0:
                        session.commit()
                        logger.info(f"Migrated {i + 1}/{len(sightings_data)} sightings")
                
                # Final commit
                session.commit()
                logger.info(f"Successfully migrated {migrated_count} sighting records")
                
        except Exception as e:
            logger.error(f"Error migrating sightings: {e}")
            self.stats['errors'] += 1
        
        return migrated_count
    
    def validate_sighting_data_integrity(self):
        """Additional validation specific to sighting data"""
        issues = []
        
        try:
            with get_db_session() as session:
                # Check for sightings with rings that don't exist in ringings table
                orphaned_sightings = session.execute("""
                    SELECT COUNT(*) FROM sightings s 
                    LEFT JOIN ringings r ON s.ring = r.ring 
                    WHERE s.ring IS NOT NULL AND r.ring IS NULL
                """).scalar()
                
                if orphaned_sightings > 0:
                    issues.append(f"Found {orphaned_sightings} sightings with rings not in ringings table")
                
                # Check for duplicate excel_ids
                duplicate_excel_ids = session.execute("""
                    SELECT excel_id, COUNT(*) as count 
                    FROM sightings 
                    WHERE excel_id IS NOT NULL
                    GROUP BY excel_id 
                    HAVING COUNT(*) > 1
                """).fetchall()
                
                if duplicate_excel_ids:
                    issues.append(f"Found {len(duplicate_excel_ids)} duplicate excel_ids in sightings")
                
                # Check for invalid coordinates in sightings
                invalid_coords = session.execute("""
                    SELECT COUNT(*) FROM sightings 
                    WHERE (lat IS NOT NULL AND (lat < -90 OR lat > 90))
                    OR (lon IS NOT NULL AND (lon < -180 OR lon > 180))
                """).scalar()
                
                if invalid_coords > 0:
                    issues.append(f"Found {invalid_coords} sightings with invalid coordinates")
        
        except Exception as e:
            issues.append(f"Error during sighting data validation: {e}")
        
        return issues
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("Starting S3 pickle to PostgreSQL migration")
        logger.info(f"Dry run mode: {self.dry_run}")
        logger.info(f"User: {self.user}")
        
        # Validate required configuration
        if not S3_BUCKET_NAME:
            logger.error("S3_BUCKET_NAME environment variable is required")
            return False
        
        # Connect to S3
        if not self.connect_s3():
            return False
        
        # Test PostgreSQL connection
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            return False
        
        # Create tables if they don't exist
        if not self.dry_run:
            create_tables()
        
        # Get initial count
        initial_sightings = get_table_count('sightings')
        logger.info(f"Initial PostgreSQL sightings count: {initial_sightings}")
        
        # Load and migrate sightings
        logger.info("Loading sightings from S3...")
        sightings_data = self.load_sightings_from_s3()
        if not sightings_data:
            logger.error("Failed to load sightings from S3")
            return False
        
        self.migrate_sightings(sightings_data)
        
        # Final count
        final_sightings = get_table_count('sightings')
        logger.info(f"Final PostgreSQL sightings count: {final_sightings}")
        
        # Print statistics
        logger.info("Migration Statistics:")
        logger.info(f"  Sightings processed: {self.stats['sightings_processed']}")
        logger.info(f"  Sightings migrated: {self.stats['sightings_migrated']}")
        logger.info(f"  Sightings skipped (duplicates): {self.stats['sightings_skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        
        # Validate data integrity if requested
        if VALIDATE_DATA and not self.dry_run:
            logger.info("Validating data integrity...")
            
            # General validation
            issues = validate_data_integrity()
            
            # Sighting-specific validation
            sighting_issues = self.validate_sighting_data_integrity()
            issues.extend(sighting_issues)
            
            if issues:
                logger.warning("Data integrity issues found:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("Data integrity validation passed")
        
        success = self.stats['errors'] == 0
        if success:
            logger.info("S3 pickle migration completed successfully")
        else:
            logger.error(f"S3 pickle migration completed with {self.stats['errors']} errors")
        
        return success


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Migrate sighting data from S3 pickle files to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual migration)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing data')
    parser.add_argument('--truncate', action='store_true', help='Truncate sightings table before migration')
    parser.add_argument('--user', default=DEFAULT_USER, help=f'User for sighting file (default: {DEFAULT_USER})')
    
    args = parser.parse_args()
    
    # Handle validate-only mode
    if args.validate_only:
        logger.info("Running data validation only...")
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            sys.exit(1)
        
        migrator = S3PickleMigrator(dry_run=True, user=args.user)
        issues = validate_data_integrity()
        sighting_issues = migrator.validate_sighting_data_integrity()
        issues.extend(sighting_issues)
        
        if issues:
            logger.error("Data integrity issues found:")
            for issue in issues:
                logger.error(f"  - {issue}")
            sys.exit(1)
        else:
            logger.info("Data integrity validation passed")
            sys.exit(0)
    
    # Handle truncate mode
    if args.truncate:
        logger.warning("Truncating sightings table before migration...")
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            sys.exit(1)
        
        try:
            truncate_table('sightings')
            logger.info("Sightings table truncated successfully")
        except Exception as e:
            logger.error(f"Error truncating sightings table: {e}")
            sys.exit(1)
    
    # Run migration
    dry_run = args.dry_run or DRY_RUN
    migrator = S3PickleMigrator(dry_run=dry_run, user=args.user)
    
    success = migrator.run_migration()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()