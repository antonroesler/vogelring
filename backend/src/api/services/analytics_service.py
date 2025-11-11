"""
Analytics service layer - migrated from AWS Lambda to use PostgreSQL
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_
from collections import defaultdict

from ...database.repositories import SightingRepository, RingingRepository
from .bird_service import BirdService
from ...database.models import Sighting as SightingDB

logger = logging.getLogger(__name__)


class SeasonalCount:
    """Data class for seasonal analysis counts"""

    def __init__(
        self,
        species: str,
        month: int,
        absolute_avg: int,
        relative_avg: float,
        q1_avg: int,
        q3_avg: int,
        max_count: int,
        recent_count: int,
    ):
        self.species = species
        self.month = month
        self.absolute_avg = absolute_avg
        self.relative_avg = relative_avg
        self.q1_avg = q1_avg
        self.q3_avg = q3_avg
        self.max_count = max_count
        self.recent_count = recent_count


class SeasonalAnalysis:
    """Data class for seasonal analysis results"""

    def __init__(self, counts: Dict[str, List[SeasonalCount]]):
        self.counts = counts


class AnalyticsService:
    """Service for analytics operations using PostgreSQL"""

    def __init__(self, db: Session):
        self.db = db
        self.sighting_repository = SightingRepository(db)
        self.ringing_repository = RingingRepository(db)

    def get_all_sightings_from_ring(self, ring: str, org_id: str) -> List[SightingDB]:
        """Get all sightings for a specific ring, sorted by date"""
        sightings = self.sighting_repository.get_by_ring(ring, org_id)
        return sorted(sightings, key=lambda x: x.date or date.min)

    def get_friends_from_ring(
        self, ring: str, org_id: str, min_shared_sightings: int = 2
    ) -> Dict[str, Any]:
        """Get friends analysis for a specific ring"""
        # Get all sightings for the target ring
        target_sightings = self.get_all_sightings_from_ring(ring, org_id)

        # Create list of (place, date) tuples for the target ring
        place_dates = [
            (sighting.place, sighting.date)
            for sighting in target_sightings
            if sighting.place and sighting.date
        ]

        if not place_dates:
            return {
                "bird": BirdService(self.db).get_bird_meta_by_ring(ring, org_id),
                "friends": [],
                "seen_status": {},
            }

        # Find all other sightings that share the same place and date
        friends = defaultdict(list)
        seen_together_ids = []

        for place, date_val in place_dates:
            # Query for sightings on the same date and place, excluding the target ring
            shared_sightings = (
                self.db.query(SightingDB)
                .filter(
                    and_(
                        SightingDB.org_id == org_id,
                        SightingDB.place == place,
                        SightingDB.date == date_val,
                        SightingDB.ring != ring,
                        SightingDB.ring.isnot(None),
                    )
                )
                .all()
            )

            for sighting in shared_sightings:
                friends[sighting.ring].append(sighting.place)
                seen_together_ids.append(str(sighting.id))

        # Filter friends with at least min_shared_sightings, then get top 10
        filtered_friends = {
            k: v for k, v in friends.items() if len(v) >= min_shared_sightings
        }
        top_friends = sorted(
            filtered_friends.items(), key=lambda x: len(x[1]), reverse=True
        )[:10]

        # Build friend metadata
        friend_metas = []
        for friend_ring, places in top_friends:
            friend_meta = BirdService(self.db).get_bird_meta_by_ring(
                friend_ring, org_id
            )
            friend_meta["count"] = len(places)
            friend_meta["places"] = list(set(places))
            friend_metas.append(friend_meta)

        # Get bird metadata for the target ring
        bird_meta = BirdService(self.db).get_bird_meta_by_ring(ring, org_id)

        # Build seen status
        seen_status = {}
        for sighting in target_sightings:
            seen_status[str(sighting.id)] = "CURRENT_BIRD"

        # Add seen together status for friend sightings
        for friend_meta in friend_metas:
            if "sightings" in friend_meta:
                for sighting in friend_meta["sightings"]:
                    sighting_id = str(sighting.get("id", ""))
                    if sighting_id in seen_together_ids:
                        seen_status[sighting_id] = "SEEN_TOGETHER"
                    else:
                        seen_status[sighting_id] = "SEEN_SEPARATE"

        return {"bird": bird_meta, "friends": friend_metas, "seen_status": seen_status}

    def get_seasonal_analysis(self, org_id: str) -> SeasonalAnalysis:
        """Get seasonal analysis of sightings"""
        # Get all sightings with species and date
        sightings = (
            self.db.query(SightingDB)
            .filter(
                and_(
                    SightingDB.org_id == org_id,
                    SightingDB.species.isnot(None),
                    SightingDB.date.isnot(None),
                )
            )
            .all()
        )

        # Group by species and year-month
        year_species_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        recent_counts = defaultdict(lambda: defaultdict(int))

        current_date = datetime.now().date()
        current_month = current_date.month
        current_year = current_date.year

        for sighting in sightings:
            species = sighting.species or "Unbekannt"
            year = sighting.date.year
            month = sighting.date.month

            # Regular counts
            year_species_counts[species][year][month] += 1

            # Recent counts (last 12 months)
            months_diff = (current_year - year) * 12 + (current_month - month)
            if 0 <= months_diff < 12:
                recent_counts[species][month] += 1

        # Calculate seasonal counts for each species
        species_seasonal_counts = {}
        for species, year_counts in year_species_counts.items():
            seasonal_counts = self._get_seasonal_counts(
                species, year_counts, recent_counts.get(species, {})
            )
            species_seasonal_counts[species] = seasonal_counts

        return SeasonalAnalysis(counts=species_seasonal_counts)

    # Bird meta logic moved to BirdService

    def _get_seasonal_counts(
        self,
        species: str,
        year_counts: Dict[int, Dict[int, int]],
        recent_counts: Dict[int, int],
    ) -> List[SeasonalCount]:
        """Calculate seasonal counts for a species"""
        # Initialize lists to store counts for each month
        month_counts = {month: [] for month in range(1, 13)}

        # Collect all counts for each month across years
        for year_data in year_counts.values():
            for month in range(1, 13):
                count = year_data.get(month, 0)
                month_counts[month].append(count)

        # Calculate statistics for each month
        seasonal_counts = []
        medians = []
        q3s = []

        for month in range(1, 13):
            counts_list = month_counts[month]
            if not counts_list:
                median = q1 = q3 = max_count = 0
            else:
                sorted_counts = sorted(counts_list)
                n = len(sorted_counts)

                # Calculate median (Q2)
                if n % 2 == 0:
                    median = (sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2
                else:
                    median = sorted_counts[n // 2]

                # Calculate Q1
                q1_pos = n // 4
                if n % 4 == 0 and q1_pos > 0:
                    q1 = (sorted_counts[q1_pos - 1] + sorted_counts[q1_pos]) / 2
                else:
                    q1 = sorted_counts[q1_pos] if q1_pos < n else 0

                # Calculate Q3
                q3_pos = (3 * n) // 4
                if n % 4 == 0 and q3_pos < n:
                    q3 = (sorted_counts[q3_pos - 1] + sorted_counts[q3_pos]) / 2
                else:
                    q3 = sorted_counts[min(q3_pos, n - 1)] if n > 0 else 0

                max_count = max(sorted_counts)

            medians.append(median)
            q3s.append(q3)

        # Find the maximum value for normalization
        max_value = max(q3s) if any(q3s) else 1

        # Create seasonal counts
        for month in range(1, 13):
            median = medians[month - 1]
            q1 = 0  # Simplified for now
            q3 = q3s[month - 1]
            max_count = max(month_counts[month]) if month_counts[month] else 0
            recent_count = recent_counts.get(month, 0)

            seasonal_count = SeasonalCount(
                species=species,
                month=month,
                absolute_avg=round(median),
                relative_avg=round(median / max_value, 2) if max_value > 0 else 0,
                q1_avg=round(q1),
                q3_avg=round(q3),
                max_count=round(max_count),
                recent_count=round(recent_count),
            )
            seasonal_counts.append(seasonal_count)

        return seasonal_counts
