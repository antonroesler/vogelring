#!/usr/bin/env python3
"""
Migration Setup Test Script

This script tests the migration setup by validating:
- Environment configuration
- AWS connectivity (DynamoDB and S3)
- PostgreSQL connectivity
- Required dependencies

Usage:
    python test_setup.py
"""

import logging
import sys
import os
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_environment_variables() -> Tuple[bool, List[str]]:
    """Test required environment variables"""
    logger.info("Testing environment variables...")
    
    required_vars = [
        'POSTGRES_PASSWORD',
        'S3_BUCKET_NAME'
    ]
    
    optional_vars = [
        'AWS_REGION',
        'DYNAMO_TABLE_NAME',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DB',
        'POSTGRES_USER'
    ]
    
    issues = []
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Required environment variable {var} is not set")
    
    # Check optional variables (warn if not set)
    for var in optional_vars:
        if not os.getenv(var):
            logger.warning(f"Optional environment variable {var} is not set (using default)")
    
    success = len(issues) == 0
    if success:
        logger.info("✅ Environment variables OK")
    else:
        logger.error("❌ Environment variable issues found")
    
    return success, issues


def test_python_dependencies() -> Tuple[bool, List[str]]:
    """Test required Python dependencies"""
    logger.info("Testing Python dependencies...")
    
    required_packages = [
        'boto3',
        'psycopg2',
        'sqlalchemy',
        'pydantic',
        'python-dotenv'
    ]
    
    issues = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            issues.append(f"Required package {package} is not installed")
    
    success = len(issues) == 0
    if success:
        logger.info("✅ Python dependencies OK")
    else:
        logger.error("❌ Python dependency issues found")
    
    return success, issues


def test_aws_connectivity() -> Tuple[bool, List[str]]:
    """Test AWS connectivity"""
    logger.info("Testing AWS connectivity...")
    
    issues = []
    
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        from config import AWS_REGION, DYNAMO_TABLE_NAME, S3_BUCKET_NAME
        
        # Test DynamoDB
        try:
            dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
            table = dynamodb.Table(DYNAMO_TABLE_NAME)
            table.load()
            logger.info(f"✅ DynamoDB table '{DYNAMO_TABLE_NAME}' accessible")
        except NoCredentialsError:
            issues.append("AWS credentials not configured")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                issues.append(f"DynamoDB table '{DYNAMO_TABLE_NAME}' not found")
            else:
                issues.append(f"DynamoDB error: {e}")
        except Exception as e:
            issues.append(f"DynamoDB connection error: {e}")
        
        # Test S3
        try:
            s3 = boto3.client('s3', region_name=AWS_REGION)
            s3.head_bucket(Bucket=S3_BUCKET_NAME)
            logger.info(f"✅ S3 bucket '{S3_BUCKET_NAME}' accessible")
        except NoCredentialsError:
            if "AWS credentials not configured" not in issues:
                issues.append("AWS credentials not configured")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                issues.append(f"S3 bucket '{S3_BUCKET_NAME}' not found")
            else:
                issues.append(f"S3 error: {e}")
        except Exception as e:
            issues.append(f"S3 connection error: {e}")
    
    except ImportError as e:
        issues.append(f"AWS SDK import error: {e}")
    
    success = len(issues) == 0
    if success:
        logger.info("✅ AWS connectivity OK")
    else:
        logger.error("❌ AWS connectivity issues found")
    
    return success, issues


def test_postgresql_connectivity() -> Tuple[bool, List[str]]:
    """Test PostgreSQL connectivity"""
    logger.info("Testing PostgreSQL connectivity...")
    
    issues = []
    
    try:
        from database import test_connection, DATABASE_URL
        
        logger.info(f"Testing connection to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
        
        if test_connection():
            logger.info("✅ PostgreSQL connection OK")
        else:
            issues.append("PostgreSQL connection failed")
    
    except ImportError as e:
        issues.append(f"PostgreSQL dependency import error: {e}")
    except Exception as e:
        issues.append(f"PostgreSQL connection error: {e}")
    
    success = len(issues) == 0
    if not success:
        logger.error("❌ PostgreSQL connectivity issues found")
    
    return success, issues


def test_database_schema() -> Tuple[bool, List[str]]:
    """Test database schema creation"""
    logger.info("Testing database schema...")
    
    issues = []
    
    try:
        from database import create_tables, get_table_count
        
        # Try to create tables
        create_tables()
        logger.info("✅ Database tables created/verified")
        
        # Check if tables exist by getting counts
        tables = ['ringings', 'sightings', 'family_tree_entries']
        for table in tables:
            try:
                count = get_table_count(table)
                logger.info(f"  {table}: {count} records")
            except Exception as e:
                issues.append(f"Error accessing table {table}: {e}")
    
    except Exception as e:
        issues.append(f"Database schema error: {e}")
    
    success = len(issues) == 0
    if success:
        logger.info("✅ Database schema OK")
    else:
        logger.error("❌ Database schema issues found")
    
    return success, issues


def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("VOGELRING MIGRATION SETUP TEST")
    logger.info("=" * 60)
    
    all_issues = []
    all_success = True
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded from .env file")
    except ImportError:
        logger.warning("python-dotenv not available, using system environment variables")
    except Exception as e:
        logger.warning(f"Error loading .env file: {e}")
    
    # Run all tests
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Python Dependencies", test_python_dependencies),
        ("AWS Connectivity", test_aws_connectivity),
        ("PostgreSQL Connectivity", test_postgresql_connectivity),
        ("Database Schema", test_database_schema),
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            success, issues = test_func()
            if not success:
                all_success = False
                all_issues.extend(issues)
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            all_success = False
            all_issues.append(f"{test_name}: {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    if all_success:
        logger.info("✅ ALL TESTS PASSED - Migration setup is ready!")
        logger.info("\nYou can now run the migration:")
        logger.info("  python migrate_all.py --dry-run  # Test migration")
        logger.info("  python migrate_all.py            # Run migration")
    else:
        logger.error("❌ SOME TESTS FAILED - Please fix the following issues:")
        for issue in all_issues:
            logger.error(f"  - {issue}")
        logger.info("\nRefer to the README.md for troubleshooting guidance.")
    
    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()