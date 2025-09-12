# Vogelring Migration Scripts

This directory contains scripts to migrate data from AWS (DynamoDB + S3) to PostgreSQL for the Vogelring application.

## Overview

The migration process consists of two main steps:
1. **DynamoDB Migration**: Migrate ringing data and family tree entries from DynamoDB to PostgreSQL
2. **S3 Pickle Migration**: Migrate sighting data from S3 pickle files to PostgreSQL

## Prerequisites

### Software Requirements
- Python 3.8+
- PostgreSQL 12+
- AWS CLI configured with appropriate credentials
- Access to the source DynamoDB table and S3 bucket

### Python Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

### Database Setup
Ensure PostgreSQL is running and accessible. The migration scripts will create the necessary tables automatically.

## Configuration

### Environment Variables
Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` with your specific configuration:

#### AWS Configuration
- `AWS_REGION`: AWS region (default: eu-central-1)
- `DYNAMO_TABLE_NAME`: DynamoDB table name (default: vogelring)
- `S3_BUCKET_NAME`: S3 bucket name (required)
- `S3_SIGHTINGS_FILE`: S3 sightings file name (default: sightings.pkl)

#### PostgreSQL Configuration
- `POSTGRES_HOST`: PostgreSQL host (default: localhost)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `POSTGRES_DB`: Database name (default: vogelring)
- `POSTGRES_USER`: Database username (default: vogelring)
- `POSTGRES_PASSWORD`: Database password (required)

#### Migration Configuration
- `BATCH_SIZE`: Records to process per batch (default: 1000)
- `DRY_RUN`: Set to 'true' for dry run mode (default: false)
- `VALIDATE_DATA`: Set to 'true' to validate data after migration (default: true)
- `DEFAULT_USER`: Default user for single-user migration (default: default)

### AWS Credentials
Ensure AWS credentials are configured via one of these methods:
- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- IAM roles (if running on EC2)

## Usage

### Complete Migration
Run the complete migration process (recommended):
```bash
python migrate_all.py
```

### Individual Migrations
Run individual migration steps:

#### DynamoDB Migration Only
```bash
python migrate_dynamodb.py
```

#### S3 Pickle Migration Only
```bash
python migrate_s3_pickle.py --user your-username
```

### Command Line Options

All scripts support these common options:

- `--dry-run`: Run in dry-run mode (no actual data changes)
- `--validate-only`: Only validate existing data integrity
- `--truncate`: Truncate tables before migration (⚠️ destructive)

#### S3 Migration Specific Options
- `--user USER`: Specify user for sighting file (default: from DEFAULT_USER env var)

### Examples

#### Dry Run Migration
Test the migration without making changes:
```bash
python migrate_all.py --dry-run
```

#### Clean Migration
Start with empty tables:
```bash
python migrate_all.py --truncate
```

#### Validate Existing Data
Check data integrity without migration:
```bash
python migrate_dynamodb.py --validate-only
python migrate_s3_pickle.py --validate-only
```

#### Migrate Specific User's Sightings
```bash
python migrate_s3_pickle.py --user john.doe
```

## Data Validation

The migration scripts include comprehensive data validation:

### DynamoDB Validation
- Duplicate ring numbers in ringings table
- NULL dates in ringing records
- Invalid coordinates (lat/lon out of range)
- NULL rings in family tree entries

### S3 Pickle Validation
- Sightings with rings not in ringings table
- Duplicate excel_ids in sightings
- Invalid coordinates in sightings
- Data type consistency

### Running Validation
Validation runs automatically after migration (if `VALIDATE_DATA=true`), or manually:
```bash
python migrate_all.py --validate-only
```

## Logging

All migration activities are logged to both console and log files:
- `migration_dynamodb.log`: DynamoDB migration log
- `migration_s3_pickle.log`: S3 pickle migration log
- `migration_complete.log`: Complete migration log

## Troubleshooting

### Common Issues

#### AWS Credentials Not Found
```
NoCredentialsError: Unable to locate credentials
```
**Solution**: Configure AWS credentials using `aws configure` or environment variables.

#### PostgreSQL Connection Failed
```
Error connecting to PostgreSQL
```
**Solution**: 
- Verify PostgreSQL is running
- Check connection parameters in `.env`
- Ensure database and user exist

#### S3 Bucket Not Found
```
S3 bucket not found
```
**Solution**: 
- Verify bucket name in configuration
- Check AWS credentials have S3 access
- Ensure bucket exists in the specified region

#### DynamoDB Table Not Found
```
Error connecting to DynamoDB
```
**Solution**:
- Verify table name in configuration
- Check AWS credentials have DynamoDB access
- Ensure table exists in the specified region

#### Memory Issues with Large Datasets
If migration fails with memory errors:
- Reduce `BATCH_SIZE` in configuration
- Run migrations separately instead of using `migrate_all.py`
- Monitor system resources during migration

### Data Issues

#### Duplicate Data
The migration scripts handle duplicates by:
- Skipping existing records (based on primary keys)
- Logging skipped records for review

#### Invalid Data Types
The scripts include data type conversion and validation:
- DynamoDB Decimal → PostgreSQL DECIMAL
- String date formats → PostgreSQL DATE
- Empty strings → NULL values

#### Missing Relationships
Some sightings may reference rings that don't exist in the ringings table. This is logged but doesn't stop migration.

## Performance Considerations

### Batch Processing
- Default batch size: 1000 records
- Adjust `BATCH_SIZE` based on available memory
- Larger batches = faster migration but more memory usage

### Database Performance
- Migration creates indexes after data insertion
- Consider temporarily disabling foreign key constraints for large datasets
- Monitor PostgreSQL performance during migration

### Network Considerations
- S3 downloads can be slow for large pickle files
- Consider running migration from AWS EC2 for better network performance
- DynamoDB scan operations may take time for large tables

## Post-Migration Steps

After successful migration:

1. **Verify Data Counts**
   ```sql
   SELECT COUNT(*) FROM ringings;
   SELECT COUNT(*) FROM sightings;
   SELECT COUNT(*) FROM family_tree_entries;
   ```

2. **Test Application Functionality**
   - Start the FastAPI backend
   - Test key endpoints
   - Verify data relationships

3. **Backup Migrated Data**
   ```bash
   pg_dump vogelring > vogelring_backup.sql
   ```

4. **Clean Up**
   - Remove AWS resources if no longer needed
   - Archive migration logs
   - Update application configuration

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review migration logs for specific error messages
3. Validate your configuration against the examples
4. Test with `--dry-run` mode first