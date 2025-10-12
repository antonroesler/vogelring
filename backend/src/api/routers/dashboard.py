"""
Dashboard API router
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc

from ...database.connection import get_db
from ...utils.auth import get_current_user
from ...database.connection import get_db
from ...database.user_models import User
from ...database.models import Sighting, Ringing
from ..services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    days: int = Query(
        30, ge=1, le=365, description="Number of days to include in recent activity"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard overview data"""

    this_week_start = date.today() - timedelta(days=date.today().weekday())
    last_week_start = this_week_start - timedelta(days=7)

    count_sightings_this_week = (
        db.query(Sighting)
        .filter(Sighting.org_id == current_user.org_id)
        .filter(Sighting.date >= this_week_start)
        .filter(Sighting.date <= date.today())
        .count()
    )
    count_sightings_last_week = (
        db.query(Sighting)
        .filter(Sighting.org_id == current_user.org_id)
        .filter(Sighting.date >= last_week_start)
        .filter(Sighting.date <= this_week_start)
        .count()
    )

    count_sightings_today = (
        db.query(Sighting)
        .filter(Sighting.org_id == current_user.org_id)
        .filter(Sighting.date == date.today())
        .count()
    )
    count_sightings_yesterday = (
        db.query(Sighting)
        .filter(Sighting.org_id == current_user.org_id)
        .filter(Sighting.date == date.today() - timedelta(days=1))
        .count()
    )

    # Count day streak of sightings
    day_streak = 0
    current_date = date.today()
    while current_date >= this_week_start:
        if (
            db.query(Sighting)
            .filter(Sighting.org_id == current_user.org_id)
            .filter(Sighting.date == current_date)
            .count()
            > 0
        ):
            day_streak += 1
        current_date -= timedelta(days=1)

    count_total_sightings = (
        db.query(Sighting).filter(Sighting.org_id == current_user.org_id).count()
    )

    count_total_unique_birds = (
        db.query(Sighting.ring)
        .filter(Sighting.org_id == current_user.org_id)
        .filter(Sighting.ring.isnot(None))
        .distinct()
        .count()
    )

    # Count top 10 species with respective sighting counts
    top_species = (
        db.query(Sighting.species, func.count(Sighting.species).label("count"))
        .filter(Sighting.org_id == current_user.org_id)
        .group_by(Sighting.species)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )
    top_species_counts = {row.species: row.count for row in top_species}

    # Count top 10 locations with respective sighting counts
    top_locations = (
        db.query(Sighting.place, func.count(Sighting.place).label("count"))
        .filter(Sighting.org_id == current_user.org_id)
        .group_by(Sighting.place)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )
    top_locations_counts = {row.place: row.count for row in top_locations}

    return {
        "count_sightings_this_week": count_sightings_this_week,
        "count_sightings_last_week": count_sightings_last_week,
        "count_sightings_today": count_sightings_today,
        "count_sightings_yesterday": count_sightings_yesterday,
        "day_streak": day_streak,
        "count_total_sightings": count_total_sightings,
        "count_total_unique_birds": count_total_unique_birds,
        "top_species": top_species_counts,
        "top_locations": top_locations_counts,
    }
