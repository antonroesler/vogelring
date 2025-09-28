#!/usr/bin/env python3
"""
Script to upsert ringing data from CSV files with proper environment variable handling.
"""

import os
import sys
import csv
from datetime import datetime
from enum import Enum
from typing import Dict, Optional
import logging

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Set up database URL from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "vogelring")
DB_USER = os.getenv("DB_USER", "vogelring")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Override the DATABASE_URL environment variable
os.environ["DATABASE_URL"] = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

from src.database.connection import get_db_session
from src.database.models import Ringing
from src.api.services.ringing_service import RingingService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RingingCols(Enum):
    """Column indices for the CSV file"""

    ring_scheme = 0  # strRingScheme
    ring = 1  # strRingNr
    species = 2  # strSpecies
    sex = 4  # strSex
    age = 5  # strAge
    date = 9  # dtmDate
    place_id = 12  # idGeoTab
    ringer = 15  # strRingerNr
    comment = 23  # strRemarks
    lon = 26  # lngLong
    lat = 27  # lngLat


def read_places(file_path: str) -> Dict[str, str]:
    """Read places mapping from CSV file"""
    places = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # Skip header
            next(f)
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) >= 4:
                    place_id = row[0]  # idGeoTab
                    place_name = row[3]  # strPlace
                    places[place_id] = place_name
        logger.info(f"Loaded {len(places)} places from {file_path}")
    except Exception as e:
        logger.error(f"Error reading places file {file_path}: {e}")
        raise
    return places


def clean_ring_number(ring: str) -> str:
    """Clean ring number by removing dots and spaces"""
    return ring.replace(".", "").replace(" ", "").strip()


def parse_sex(sex_str: str) -> int:
    """Convert sex string to integer"""
    try:
        return int(sex_str)
    except ValueError:
        # Handle non-numeric sex values
        sex_str = sex_str.upper().strip()
        if sex_str in ["M", "MALE", "1"]:
            return 1
        elif sex_str in ["W", "F", "FEMALE", "2"]:
            return 2
        else:
            return 0  # Unknown


def parse_age(age_str: str) -> int:
    """Convert age string to integer"""
    try:
        return int(age_str)
    except ValueError:
        # Handle non-numeric age values
        age_str = age_str.upper().strip()
        # You might want to add specific mappings here if needed
        return 0  # Unknown


def convert_csv_row_to_ringing(
    row: list, place_map: Dict[str, str]
) -> Optional[Ringing]:
    """Convert a CSV row to a Ringing object"""
    try:
        # Parse date from string
        date_str = row[RingingCols.date.value]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()

        # Get place name from place_id
        place_id = row[RingingCols.place_id.value]
        place_name = place_map.get(place_id, f"Unknown Place ({place_id})")

        # Clean and validate data
        ring = clean_ring_number(row[RingingCols.ring.value])
        if not ring:
            logger.warning(f"Empty ring number in row, skipping")
            return None

        # Parse coordinates
        try:
            lat = float(row[RingingCols.lat.value])
            lon = float(row[RingingCols.lon.value])
        except (ValueError, IndexError):
            logger.warning(f"Invalid coordinates for ring {ring}, using default")
            lat = 0.0
            lon = 0.0

        # Get comment (remarks)
        comment = (
            row[RingingCols.comment.value].strip()
            if len(row) > RingingCols.comment.value
            else ""
        )

        # Create Ringing object
        ringing = Ringing(
            ring=ring,
            ring_scheme=row[RingingCols.ring_scheme.value],
            species=row[RingingCols.species.value],
            date=date_obj,
            place=place_name,
            lat=lat,
            lon=lon,
            ringer=row[RingingCols.ringer.value],
            sex=parse_sex(row[RingingCols.sex.value]),
            age=parse_age(row[RingingCols.age.value]),
            comment=comment if comment else None,
        )

        return ringing

    except Exception as e:
        logger.error(f"Error converting row to ringing: {e}")
        logger.error(f"Row data: {row}")
        return None


def upsert_ringing_with_comment_only(
    service: RingingService, ring: str, comment: str
) -> bool:
    """Update only the comment for an existing ringing"""
    try:
        # Get existing ringing
        existing = service.get_ringing_by_ring(ring)
        if not existing:
            return False

        # Update only the comment using the repository directly
        update_data = {"comment": comment if comment else None}
        service.repository.upsert_ringing(ring, **update_data)

        logger.info(f"Updated comment for ring {ring}")
        return True

    except Exception as e:
        logger.error(f"Error updating comment for ring {ring}: {e}")
        return False


def dry_run_analysis(csv_file: str, places_file: str, max_rows: int = None):
    """Dry run to analyze what would happen during upsert"""
    logger.info("Starting dry run analysis...")
    logger.info(
        f"Database URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Read places mapping
    place_map = read_places(places_file)

    # Statistics
    stats = {
        "total_rows": 0,
        "skipped_rows": 0,
        "would_create_new": 0,
        "would_update_comment": 0,
        "would_skip_no_change": 0,
        "errors": 0,
        "sample_new_rings": [],
        "sample_updated_rings": [],
    }

    # Get database session
    with get_db_session() as db:
        service = RingingService(db)

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                # Skip header
                next(f)
                reader = csv.reader(f, delimiter=";")

                for row_num, row in enumerate(reader, start=2):
                    stats["total_rows"] += 1

                    # Stop if max_rows reached
                    if max_rows and stats["total_rows"] > max_rows:
                        break

                    if len(row) < max([col.value for col in RingingCols]) + 1:
                        logger.warning(f"Row {row_num}: Insufficient columns")
                        stats["skipped_rows"] += 1
                        continue

                    # Convert row to ringing object
                    ringing = convert_csv_row_to_ringing(row, place_map)
                    if not ringing:
                        stats["skipped_rows"] += 1
                        continue

                    try:
                        # Check if ringing already exists
                        existing = service.get_ringing_by_ring(ringing.ring)

                        if existing:
                            # Ring exists: check if comment would change
                            if existing.comment != ringing.comment:
                                stats["would_update_comment"] += 1
                                if len(stats["sample_updated_rings"]) < 5:
                                    stats["sample_updated_rings"].append(
                                        {
                                            "ring": ringing.ring,
                                            "old_comment": existing.comment,
                                            "new_comment": ringing.comment,
                                        }
                                    )
                                logger.debug(f"Would update comment for {ringing.ring}")
                            else:
                                stats["would_skip_no_change"] += 1
                                logger.debug(f"No change needed for {ringing.ring}")
                        else:
                            # Ring doesn't exist: would create new
                            stats["would_create_new"] += 1
                            if len(stats["sample_new_rings"]) < 5:
                                stats["sample_new_rings"].append(
                                    {
                                        "ring": ringing.ring,
                                        "species": ringing.species,
                                        "place": ringing.place,
                                        "comment": ringing.comment,
                                    }
                                )
                            logger.debug(f"Would create new ringing for {ringing.ring}")

                    except Exception as e:
                        logger.error(
                            f"Row {row_num}: Error checking ring {ringing.ring}: {e}"
                        )
                        stats["errors"] += 1

                    # Log progress
                    if stats["total_rows"] % 500 == 0:
                        logger.info(f"Analyzed {stats['total_rows']} rows...")

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

    # Print analysis results
    logger.info("=" * 60)
    logger.info("DRY RUN ANALYSIS RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total rows analyzed: {stats['total_rows']}")
    logger.info(f"Skipped rows: {stats['skipped_rows']}")
    logger.info(f"Would create new ringings: {stats['would_create_new']}")
    logger.info(f"Would update comments: {stats['would_update_comment']}")
    logger.info(f"Would skip (no changes): {stats['would_skip_no_change']}")
    logger.info(f"Errors: {stats['errors']}")

    if stats["sample_new_rings"]:
        logger.info("\nSample new ringings that would be created:")
        for sample in stats["sample_new_rings"]:
            logger.info(
                f"  Ring: {sample['ring']}, Species: {sample['species']}, Comment: '{sample['comment']}'"
            )

    if stats["sample_updated_rings"]:
        logger.info("\nSample comment updates that would happen:")
        for sample in stats["sample_updated_rings"]:
            logger.info(f"  Ring: {sample['ring']}")
            logger.info(f"    Old: '{sample['old_comment']}'")
            logger.info(f"    New: '{sample['new_comment']}'")

    logger.info("=" * 60)

    return stats


def upsert_ringings_from_csv(csv_file: str, places_file: str):
    """Main function to upsert ringings from CSV"""
    logger.info("Starting ringing upsert process...")
    logger.info(
        f"Database URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Read places mapping
    place_map = read_places(places_file)

    # Statistics
    stats = {
        "total_rows": 0,
        "skipped_rows": 0,
        "new_ringings": 0,
        "updated_comments": 0,
        "errors": 0,
    }

    # Get database session
    with get_db_session() as db:
        service = RingingService(db)

        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                # Skip header
                next(f)
                reader = csv.reader(f, delimiter=";")

                for row_num, row in enumerate(
                    reader, start=2
                ):  # Start at 2 because of header
                    stats["total_rows"] += 1

                    if len(row) < max([col.value for col in RingingCols]) + 1:
                        logger.warning(f"Row {row_num}: Insufficient columns, skipping")
                        stats["skipped_rows"] += 1
                        continue

                    # Convert row to ringing object
                    ringing = convert_csv_row_to_ringing(row, place_map)
                    if not ringing:
                        stats["skipped_rows"] += 1
                        continue

                    try:
                        # Check if ringing already exists
                        existing = service.get_ringing_by_ring(ringing.ring)

                        if existing:
                            # Ring exists: only update comment if it's different
                            if existing.comment != ringing.comment:
                                success = upsert_ringing_with_comment_only(
                                    service, ringing.ring, ringing.comment
                                )
                                if success:
                                    stats["updated_comments"] += 1
                                    logger.info(
                                        f"Row {row_num}: Updated comment for existing ring {ringing.ring}"
                                    )
                                else:
                                    stats["errors"] += 1
                            else:
                                logger.debug(
                                    f"Row {row_num}: Ring {ringing.ring} comment unchanged, skipping"
                                )
                        else:
                            # Ring doesn't exist: create new ringing
                            ringing_data = {
                                "ring": ringing.ring,
                                "ring_scheme": ringing.ring_scheme,
                                "species": ringing.species,
                                "date": ringing.date,
                                "place": ringing.place,
                                "lat": ringing.lat,
                                "lon": ringing.lon,
                                "ringer": ringing.ringer,
                                "sex": ringing.sex,
                                "age": ringing.age,
                                "comment": ringing.comment,
                            }

                            created = service.upsert_ringing(ringing_data)
                            stats["new_ringings"] += 1
                            logger.info(
                                f"Row {row_num}: Created new ringing for ring {ringing.ring}"
                            )

                    except Exception as e:
                        logger.error(
                            f"Row {row_num}: Error processing ring {ringing.ring}: {e}"
                        )
                        stats["errors"] += 1

                    # Log progress every 100 rows
                    if stats["total_rows"] % 100 == 0:
                        logger.info(f"Processed {stats['total_rows']} rows...")

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise

    # Print final statistics
    logger.info("=" * 60)
    logger.info("UPSERT COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Total rows processed: {stats['total_rows']}")
    logger.info(f"Skipped rows: {stats['skipped_rows']}")
    logger.info(f"New ringings created: {stats['new_ringings']}")
    logger.info(f"Comments updated: {stats['updated_comments']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 60)

    return stats


if __name__ == "__main__":
    # File paths
    csv_file = "/Users/anton/Desktop/tblRingingNew.csv"
    places_file = "/Users/anton/Desktop/tblGeoTab.csv"

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "dry-run":
            max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else None
            try:
                stats = dry_run_analysis(csv_file, places_file, max_rows)
                logger.info("Dry run completed successfully!")
            except Exception as e:
                logger.error(f"Dry run failed: {e}")
                sys.exit(1)
        else:
            logger.error("Usage: python upsert_with_env.py [dry-run [max_rows]]")
            sys.exit(1)
    else:
        # Full upsert
        try:
            stats = upsert_ringings_from_csv(csv_file, places_file)

            if stats["errors"] > 0:
                logger.warning(f"Completed with {stats['errors']} errors")
                sys.exit(1)
            else:
                logger.info("All ringings processed successfully!")

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)


