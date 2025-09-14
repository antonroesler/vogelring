"""
Analytics API router
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ...database.connection import get_db
from ..services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/analytics/history/{ring}")
async def get_all_sightings_from_ring(
    ring: str,
    db: Session = Depends(get_db)
):
    """Get all sightings history for a specific ring"""
    service = AnalyticsService(db)
    sightings = service.get_all_sightings_from_ring(ring)
    return sightings

@router.get("/analytics/friends/{ring}")
async def get_friends_from_ring(
    ring: str,
    min_shared_sightings: int = Query(2, description="Minimum shared sightings"),
    db: Session = Depends(get_db)
):
    """Get friends analysis for a specific ring"""
    service = AnalyticsService(db)
    friends_data = service.get_friends_from_ring(ring, min_shared_sightings)
    return friends_data

@router.get("/analytics/groups/{ring}")
async def get_groups_from_ring(
    ring: str,
    min_shared_sightings: int = Query(2, description="Minimum shared sightings"),
    db: Session = Depends(get_db)
):
    """Get groups/friends analysis for a specific ring (alias for friends endpoint)"""
    service = AnalyticsService(db)
    friends_data = service.get_friends_from_ring(ring, min_shared_sightings)
    return friends_data

@router.get("/seasonal-analysis")
async def get_seasonal_analysis(db: Session = Depends(get_db)):
    """Get seasonal analysis data"""
    service = AnalyticsService(db)
    analysis = service.get_seasonal_analysis()
    
    # Convert SeasonalCount objects to dictionaries
    result = {}
    for species, seasonal_counts in analysis.counts.items():
        result[species] = []
        for count in seasonal_counts:
            result[species].append({
                "species": count.species,
                "month": count.month,
                "absolute_avg": count.absolute_avg,
                "relative_avg": count.relative_avg,
                "q1_avg": count.q1_avg,
                "q3_avg": count.q3_avg,
                "max_count": count.max_count,
                "recent_count": count.recent_count
            })
    
    return {"counts": result}