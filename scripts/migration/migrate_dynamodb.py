#!/usr/bin/env python3
"""
DynamoDB to PostgreSQL Migration Script

This script migrates ringing data and family tree entries from DynamoDB to PostgreSQL.
It handles data validation, batch processing, and integrity checks.

Usage:
    python migrate_dynamodb.py [--dry-run] [--validate-only] [--truncate]

Environment Variables:
    AWS_REGION: AWS region for DynamoDB (default: eu-central-1)
    DYNAMO_TABLE_NAME: DynamoDB table name (default: vogelring)
    POSTGRES_HOST: PostgreSQL host (default: localhost)
    POSTGRES_PORT: PostgreSQL port (default: 5432)
    POSTGRES_DB: PostgreSQL database name (default: vogelring)
    POSTGRES_USER: PostgreSQL username (default: vogelring)
    POSTGRES_PASSWORD: PostgreSQL password (required)
    DRY_RUN: Set to 'true' for dry run mode (default: false)
    VALIDATE_DATA: Set to 'true' to validate data after migration (default: true)
"""

import logging
import sys
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError
from decimal import Decimal
import json

from config import (
    AWS_REGION, DYNAMO_TABLE_NAME, BATCH_SIZE, DRY_RUN, VALIDATE_DATA, 
    FAMILY_TREE_SUFFIX
)
from models import Ringing, FamilyTreeEntry
from database import (
    create_tables, test_connection, get_db_session, get_table_count,
    truncate_table, validate_data_integrity, RingingDB, FamilyTreeEntryDB
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_dynamodb.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DynamoDBMigrator:
    """Handles migration from DynamoDB to PostgreSQL"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.dynamodb = None
        self.table = None
        self.stats = {
            'ringings_processed': 0,
            'ringings_migrated': 0,
            'family_entries_processed': 0,
            'family_entries_migrated': 0,
            'errors': 0
        }
    
    def connect_dynamodb(self) -> bool:
        """Connect to DynamoDB"""
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            self.table = self.dynamodb.Table(DYNAMO_TABLE_NAME)
            
            # Test connection by describing the table
            self.table.load()
            logger.info(f"Connected to DynamoDB table: {DYNAMO_TABLE_NAME}")
            return True
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS credentials.")
            return False
        except ClientError as e:
            logger.error(f"Error connecting to DynamoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to DynamoDB: {e}")
            return False
    
    def scan_ringings(self) -> List[Dict[str, Any]]:
        """Scan DynamoDB table for ringing records (excluding family tree entries)"""
        ringings = []
        
        try:
            # Use scan with filter to exclude family tree entries
            response = self.table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('ring').not_exists() | 
                                ~boto3.dynamodb.conditions.Attr('ring').contains(FAMILY_TREE_SUFFIX)
            )
            
            ringings.extend(response.get('Items', []))
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('ring').not_exists() | 
                                    ~boto3.dynamodb.conditions.Attr('ring').contains(FAMILY_TREE_SUFFIX),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                ringings.extend(response.get('Items', []))
            
            logger.info(f"Found {len(ringings)} ringing records in DynamoDB")
            return ringings
            
        except ClientError as e:
            logger.error(f"Error scanning DynamoDB for ringings: {e}")
            return []
    
    def scan_family_tree_entries(self) -> List[Dict[str, Any]]:
        """Scan DynamoDB table for family tree entries"""
        family_entries = []
        
        try:
            # Use scan with filter to get only family tree entries
            response = self.table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('ring').contains(FAMILY_TREE_SUFFIX)
            )
            
            family_entries.extend(response.get('Items', []))
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                response = self.table.scan(
                    FilterExpression=boto3.dynamodb.conditions.Attr('ring').contains(FAMILY_TREE_SUFFIX),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                family_entries.extend(response.get('Items', []))
            
            logger.info(f"Found {len(family_entries)} family tree entries in DynamoDB")
            return family_entries
            
        except ClientError as e:
            logger.error(f"Error scanning DynamoDB for family tree entries: {e}")
            return []
    
    def convert_dynamodb_item_to_ringing(self, item: Dict[str, Any]) -> Optional[Ringing]:
        """Convert DynamoDB item to Ringing model"""
        try:
            # Convert DynamoDB Decimal types to float
            if 'lat' in item and isinstance(item['lat'], Decimal):
                item['lat'] = float(item['lat'])
            if 'lon' in item and isinstance(item['lon'], Decimal):
                item['lon'] = float(item['lon'])
            
            # Convert date string to date object if needed
            if 'date' in item and isinstance(item['date'], str):
                item['date'] = datetime.fromisoformat(item['date']).date()
            
            return Ringing(**item)
            
        except Exception as e:
            logger.error(f"Error converting DynamoDB item to Ringing: {e}")
            logger.error(f"Item data: {json.dumps(item, default=str)}")
            return None
    
    def convert_dynamodb_item_to_family_entry(self, item: Dict[str, Any]) -> Optional[FamilyTreeEntry]:
        """Convert DynamoDB item to FamilyTreeEntry model"""
        try:
            # Remove the family tree suffix from the ring
            if 'ring' in item and item['ring'].endswith(FAMILY_TREE_SUFFIX):
                item['ring'] = item['ring'][:-len(FAMILY_TREE_SUFFIX)]
            
            # Ensure lists exist for relationships
            if 'partners' not in item:
                item['partners'] = []
            if 'children' not in item:
                item['children'] = []
            if 'parents' not in item:
                item['parents'] = []
            
            return FamilyTreeEntry(**item)
            
        except Exception as e:
            logger.error(f"Error converting DynamoDB item to FamilyTreeEntry: {e}")
            logger.error(f"Item data: {json.dumps(item, default=str)}")
            return None
    
    def migrate_ringings(self, ringings: List[Dict[str, Any]]) -> int:
        """Migrate ringing records to PostgreSQL"""
        migrated_count = 0
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {len(ringings)} ringing records")
            return len(ringings)
        
        try:
            with get_db_session() as session:
                for i, item in enumerate(ringings):
                    self.stats['ringings_processed'] += 1
                    
                    # Convert DynamoDB item to Pydantic model
                    ringing = self.convert_dynamodb_item_to_ringing(item)
                    if not ringing:
                        self.stats['errors'] += 1
                        continue
                    
                    # Check if record already exists
                    existing = session.query(RingingDB).filter_by(ring=ringing.ring).first()
                    if existing:
                        logger.debug(f"Ringing {ringing.ring} already exists, skipping")
                        continue
                    
                    # Create database record
                    db_ringing = RingingDB(
                        ring=ringing.ring,
                        ring_scheme=ringing.ring_scheme,
                        species=ringing.species,
                        date=ringing.date,
                        place=ringing.place,
                        lat=ringing.lat,
                        lon=ringing.lon,
                        ringer=ringing.ringer,
                        sex=ringing.sex,
                        age=ringing.age,
                        status=ringing.status.value if ringing.status else None
                    )
                    
                    session.add(db_ringing)
                    migrated_count += 1
                    self.stats['ringings_migrated'] += 1
                    
                    # Commit in batches
                    if (i + 1) % BATCH_SIZE == 0:
                        session.commit()
                        logger.info(f"Migrated {i + 1}/{len(ringings)} ringings")
                
                # Final commit
                session.commit()
                logger.info(f"Successfully migrated {migrated_count} ringing records")
                
        except Exception as e:
            logger.error(f"Error migrating ringings: {e}")
            self.stats['errors'] += 1
        
        return migrated_count
    
    def migrate_family_tree_entries(self, family_entries: List[Dict[str, Any]]) -> int:
        """Migrate family tree entries to PostgreSQL"""
        migrated_count = 0
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {len(family_entries)} family tree entries")
            return len(family_entries)
        
        try:
            with get_db_session() as session:
                for i, item in enumerate(family_entries):
                    self.stats['family_entries_processed'] += 1
                    
                    # Convert DynamoDB item to Pydantic model
                    family_entry = self.convert_dynamodb_item_to_family_entry(item)
                    if not family_entry:
                        self.stats['errors'] += 1
                        continue
                    
                    # Check if record already exists
                    existing = session.query(FamilyTreeEntryDB).filter_by(ring=family_entry.ring).first()
                    if existing:
                        logger.debug(f"Family tree entry {family_entry.ring} already exists, skipping")
                        continue
                    
                    # Create database record
                    db_family_entry = FamilyTreeEntryDB(
                        ring=family_entry.ring,
                        partners=[p.model_dump() for p in family_entry.partners],
                        children=[c.model_dump() for c in family_entry.children],
                        parents=[p.model_dump() for p in family_entry.parents]
                    )
                    
                    session.add(db_family_entry)
                    migrated_count += 1
                    self.stats['family_entries_migrated'] += 1
                    
                    # Commit in batches
                    if (i + 1) % BATCH_SIZE == 0:
                        session.commit()
                        logger.info(f"Migrated {i + 1}/{len(family_entries)} family tree entries")
                
                # Final commit
                session.commit()
                logger.info(f"Successfully migrated {migrated_count} family tree entries")
                
        except Exception as e:
            logger.error(f"Error migrating family tree entries: {e}")
            self.stats['errors'] += 1
        
        return migrated_count
    
    def run_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("Starting DynamoDB to PostgreSQL migration")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        # Connect to DynamoDB
        if not self.connect_dynamodb():
            return False
        
        # Test PostgreSQL connection
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            return False
        
        # Create tables if they don't exist
        if not self.dry_run:
            create_tables()
        
        # Get initial counts
        initial_ringings = get_table_count('ringings')
        initial_family_entries = get_table_count('family_tree_entries')
        logger.info(f"Initial PostgreSQL counts - Ringings: {initial_ringings}, Family entries: {initial_family_entries}")
        
        # Scan and migrate ringings
        logger.info("Scanning DynamoDB for ringing records...")
        ringings = self.scan_ringings()
        if ringings:
            self.migrate_ringings(ringings)
        
        # Scan and migrate family tree entries
        logger.info("Scanning DynamoDB for family tree entries...")
        family_entries = self.scan_family_tree_entries()
        if family_entries:
            self.migrate_family_tree_entries(family_entries)
        
        # Final counts
        final_ringings = get_table_count('ringings')
        final_family_entries = get_table_count('family_tree_entries')
        logger.info(f"Final PostgreSQL counts - Ringings: {final_ringings}, Family entries: {final_family_entries}")
        
        # Print statistics
        logger.info("Migration Statistics:")
        logger.info(f"  Ringings processed: {self.stats['ringings_processed']}")
        logger.info(f"  Ringings migrated: {self.stats['ringings_migrated']}")
        logger.info(f"  Family entries processed: {self.stats['family_entries_processed']}")
        logger.info(f"  Family entries migrated: {self.stats['family_entries_migrated']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        
        # Validate data integrity if requested
        if VALIDATE_DATA and not self.dry_run:
            logger.info("Validating data integrity...")
            issues = validate_data_integrity()
            if issues:
                logger.warning("Data integrity issues found:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
            else:
                logger.info("Data integrity validation passed")
        
        success = self.stats['errors'] == 0
        if success:
            logger.info("DynamoDB migration completed successfully")
        else:
            logger.error(f"DynamoDB migration completed with {self.stats['errors']} errors")
        
        return success


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Migrate data from DynamoDB to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual migration)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing data')
    parser.add_argument('--truncate', action='store_true', help='Truncate tables before migration')
    
    args = parser.parse_args()
    
    # Handle validate-only mode
    if args.validate_only:
        logger.info("Running data validation only...")
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            sys.exit(1)
        
        issues = validate_data_integrity()
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
        logger.warning("Truncating tables before migration...")
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            sys.exit(1)
        
        try:
            truncate_table('family_tree_entries')
            truncate_table('ringings')
            logger.info("Tables truncated successfully")
        except Exception as e:
            logger.error(f"Error truncating tables: {e}")
            sys.exit(1)
    
    # Run migration
    dry_run = args.dry_run or DRY_RUN
    migrator = DynamoDBMigrator(dry_run=dry_run)
    
    success = migrator.run_migration()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()