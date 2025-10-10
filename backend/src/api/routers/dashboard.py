"""
Dashboard API router
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy import func, desc

from ...database.connection import get_db
from ...utils.auth import get_current_user, get_db_with_org
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
    db: Session = Depends(get_db_with_org),
):
    """Get dashboard overview data"""

    # Calculate date range for recent activity
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Get total counts
    total_sightings = db.query(Sighting).count()
    total_ringings = db.query(Ringing).count()

    # Get recent activity counts
    recent_sightings = (
        db.query(Sighting)
        .filter(Sighting.date >= start_date)
        .filter(Sighting.date <= end_date)
        .count()
    )

    recent_ringings = (
        db.query(Ringing)
        .filter(Ringing.date >= start_date)
        .filter(Ringing.date <= end_date)
        .count()
    )

    # Get unique species counts
    total_species = (
        db.query(Sighting.species)
        .filter(Sighting.species.isnot(None))
        .distinct()
        .count()
    )

    recent_species = (
        db.query(Sighting.species)
        .filter(Sighting.date >= start_date)
        .filter(Sighting.date <= end_date)
        .filter(Sighting.species.isnot(None))
        .distinct()
        .count()
    )

    # Get top species in recent period
    top_species = (
        db.query(Sighting.species, func.count(Sighting.species).label("count"))
        .filter(Sighting.date >= start_date)
        .filter(Sighting.date <= end_date)
        .filter(Sighting.species.isnot(None))
        .group_by(Sighting.species)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    # Get top locations in recent period
    top_locations = (
        db.query(Sighting.place, func.count(Sighting.place).label("count"))
        .filter(Sighting.date >= start_date)
        .filter(Sighting.date <= end_date)
        .filter(Sighting.place.isnot(None))
        .group_by(Sighting.place)
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    # Get daily activity for the period (last 30 days max for chart)
    chart_days = min(days, 30)
    chart_start = end_date - timedelta(days=chart_days)

    daily_activity = (
        db.query(Sighting.date, func.count(Sighting.id).label("sightings_count"))
        .filter(Sighting.date >= chart_start)
        .filter(Sighting.date <= end_date)
        .group_by(Sighting.date)
        .order_by(Sighting.date)
        .all()
    )

    # Convert to dict for easier frontend consumption
    activity_by_date = {str(row.date): row.sightings_count for row in daily_activity}

    # Fill in missing dates with 0
    current_date = chart_start
    while current_date <= end_date:
        date_str = str(current_date)
        if date_str not in activity_by_date:
            activity_by_date[date_str] = 0
        current_date += timedelta(days=1)

    return {
        "overview": {
            "total_sightings": total_sightings,
            "total_ringings": total_ringings,
            "total_species": total_species,
            "recent_sightings": recent_sightings,
            "recent_ringings": recent_ringings,
            "recent_species": recent_species,
            "period_days": days,
        },
        "top_species": [
            {"species": row.species, "count": row.count} for row in top_species
        ],
        "top_locations": [
            {"location": row.place, "count": row.count} for row in top_locations
        ],
        "daily_activity": activity_by_date,
        "generated_at": datetime.now().isoformat(),
    }


@router.get("/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get quick dashboard summary"""

    total_sightings = db.query(Sighting).count()
    total_ringings = db.query(Ringing).count()

    # Get date ranges
    sighting_dates = (
        db.query(func.min(Sighting.date), func.max(Sighting.date))
        .filter(Sighting.date.isnot(None))
        .first()
    )

    ringing_dates = db.query(func.min(Ringing.date), func.max(Ringing.date)).first()

    return {
        "totals": {"sightings": total_sightings, "ringings": total_ringings},
        "date_ranges": {
            "sightings": {
                "earliest": sighting_dates[0].isoformat()
                if sighting_dates[0]
                else None,
                "latest": sighting_dates[1].isoformat() if sighting_dates[1] else None,
            },
            "ringings": {
                "earliest": ringing_dates[0].isoformat() if ringing_dates[0] else None,
                "latest": ringing_dates[1].isoformat() if ringing_dates[1] else None,
            },
        },
    }
