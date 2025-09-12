#!/usr/bin/env python3
"""
Complete Migration Script

This script runs both DynamoDB and S3 pickle migrations in the correct order.
It provides a single entry point for the complete migration process.

Usage:
    python migrate_all.py [--dry-run] [--validate-only] [--truncate] [--user USER]

Environment Variables:
    See migrate_dynamodb.py and migrate_s3_pickle.py for required environment variables.
"""

import logging
import sys
import argparse
from datetime import datetime

from config import DRY_RUN, DEFAULT_USER
from migrate_dynamodb import DynamoDBMigrator
from migrate_s3_pickle import S3PickleMigrator
from database import test_connection, get_table_count, truncate_table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_complete.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def run_complete_migration(dry_run: bool = False, user: str = DEFAULT_USER) -> bool:
    """Run the complete migration process"""
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("STARTING COMPLETE VOGELRING MIGRATION")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time}")
    logger.info(f"Dry run mode: {dry_run}")
    logger.info(f"User: {user}")
    
    # Test PostgreSQL connection first
    if not test_connection():
        logger.error("PostgreSQL connection failed - aborting migration")
        return False
    
    # Get initial counts
    initial_ringings = get_table_count('ringings')
    initial_family_entries = get_table_count('family_tree_entries')
    initial_sightings = get_table_count('sightings')
    
    logger.info("Initial PostgreSQL counts:")
    logger.info(f"  Ringings: {initial_ringings}")
    logger.info(f"  Family tree entries: {initial_family_entries}")
    logger.info(f"  Sightings: {initial_sightings}")
    
    success = True
    
    # Step 1: Migrate DynamoDB data (ringings and family tree entries)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 1: MIGRATING DYNAMODB DATA")
    logger.info("=" * 60)
    
    dynamodb_migrator = DynamoDBMigrator(dry_run=dry_run)
    dynamodb_success = dynamodb_migrator.run_migration()
    
    if not dynamodb_success:
        logger.error("DynamoDB migration failed")
        success = False
    else:
        logger.info("DynamoDB migration completed successfully")
    
    # Step 2: Migrate S3 pickle data (sightings)
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: MIGRATING S3 PICKLE DATA")
    logger.info("=" * 60)
    
    s3_migrator = S3PickleMigrator(dry_run=dry_run, user=user)
    s3_success = s3_migrator.run_migration()
    
    if not s3_success:
        logger.error("S3 pickle migration failed")
        success = False
    else:
        logger.info("S3 pickle migration completed successfully")
    
    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("MIGRATION SUMMARY")
    logger.info("=" * 80)
    
    # Get final counts
    final_ringings = get_table_count('ringings')
    final_family_entries = get_table_count('family_tree_entries')
    final_sightings = get_table_count('sightings')
    
    logger.info("Final PostgreSQL counts:")
    logger.info(f"  Ringings: {final_ringings} (added: {final_ringings - initial_ringings})")
    logger.info(f"  Family tree entries: {final_family_entries} (added: {final_family_entries - initial_family_entries})")
    logger.info(f"  Sightings: {final_sightings} (added: {final_sightings - initial_sightings})")
    
    logger.info(f"\nMigration duration: {duration}")
    logger.info(f"End time: {end_time}")
    
    if success:
        logger.info("✅ COMPLETE MIGRATION SUCCESSFUL")
    else:
        logger.error("❌ MIGRATION COMPLETED WITH ERRORS")
    
    # Combined statistics
    total_processed = (
        dynamodb_migrator.stats['ringings_processed'] + 
        dynamodb_migrator.stats['family_entries_processed'] + 
        s3_migrator.stats['sightings_processed']
    )
    total_migrated = (
        dynamodb_migrator.stats['ringings_migrated'] + 
        dynamodb_migrator.stats['family_entries_migrated'] + 
        s3_migrator.stats['sightings_migrated']
    )
    total_errors = dynamodb_migrator.stats['errors'] + s3_migrator.stats['errors']
    
    logger.info("\nCombined Statistics:")
    logger.info(f"  Total records processed: {total_processed}")
    logger.info(f"  Total records migrated: {total_migrated}")
    logger.info(f"  Total errors: {total_errors}")
    
    logger.info("=" * 80)
    
    return success


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run complete migration from AWS to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual migration)')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing data')
    parser.add_argument('--truncate', action='store_true', help='Truncate all tables before migration')
    parser.add_argument('--user', default=DEFAULT_USER, help=f'User for sighting file (default: {DEFAULT_USER})')
    
    args = parser.parse_args()
    
    # Handle validate-only mode
    if args.validate_only:
        logger.info("Running data validation only...")
        
        # Run both validators
        dynamodb_migrator = DynamoDBMigrator(dry_run=True)
        s3_migrator = S3PickleMigrator(dry_run=True, user=args.user)
        
        # This would run the validation parts of both migrators
        # For now, just inform the user to run individual scripts
        logger.info("For validation-only mode, please run:")
        logger.info("  python migrate_dynamodb.py --validate-only")
        logger.info("  python migrate_s3_pickle.py --validate-only --user " + args.user)
        sys.exit(0)
    
    # Handle truncate mode
    if args.truncate:
        logger.warning("Truncating ALL tables before migration...")
        if not test_connection():
            logger.error("PostgreSQL connection failed")
            sys.exit(1)
        
        try:
            # Order matters due to foreign key constraints
            truncate_table('sightings')
            truncate_table('family_tree_entries')
            truncate_table('ringings')
            logger.info("All tables truncated successfully")
        except Exception as e:
            logger.error(f"Error truncating tables: {e}")
            sys.exit(1)
    
    # Run complete migration
    dry_run = args.dry_run or DRY_RUN
    success = run_complete_migration(dry_run=dry_run, user=args.user)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()