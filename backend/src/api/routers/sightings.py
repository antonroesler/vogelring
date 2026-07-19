"""
Sightings API router
"""

import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date as DateType
from pydantic import BaseModel

from ...utils.auth import get_current_user
from ...database.connection import get_db
from ...database.user_models import User
from ...database.models import Sighting as SightingDB
from ...utils.sighting_coding import ring_age_label, ring_sex_label
from ...utils.ring_places import lookup_place
from ..services.sighting_service import SightingService

router = APIRouter()


class SightingCreate(BaseModel):
    """Pydantic model for creating sightings"""

    excel_id: int | None = None
    comment: str | None = None
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    age: int | None = None  # RING/EURING code (see utils.sighting_coding)
    sex: int | None = None  # 0 unbekannt, 1 männlich, 2 weiblich
    date: DateType | None = None
    large_group_size: int | None = None
    small_group_size: int | None = None
    partner: str | None = None
    breed_size: int | None = None
    family_size: int | None = None
    pair: str | None = None
    status: str | None = None
    melder: str | None = None
    melded: bool | None = None
    place: str | None = None
    area: str | None = None
    lat: float | None = None
    lon: float | None = None
    is_exact_location: bool | None = False
    habitat: str | None = None
    field_fruit: str | None = None


class SightingUpdate(BaseModel):
    """Pydantic model for updating sightings"""

    id: str
    excel_id: int | None = None
    comment: str | None = None
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    age: int | None = None  # RING/EURING code (see utils.sighting_coding)
    sex: int | None = None  # 0 unbekannt, 1 männlich, 2 weiblich
    date: DateType | None = None
    large_group_size: int | None = None
    small_group_size: int | None = None
    partner: str | None = None
    breed_size: int | None = None
    family_size: int | None = None
    pair: str | None = None
    status: str | None = None
    melder: str | None = None
    melded: bool | None = None
    place: str | None = None
    area: str | None = None
    lat: float | None = None
    lon: float | None = None
    is_exact_location: bool | None = False
    habitat: str | None = None
    field_fruit: str | None = None


@router.get("/sightings/count")
async def get_sightings_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get total count of sightings"""
    service = SightingService(db)
    return {"count": service.get_sightings_count(current_user.org_id)}


@router.get("/sightings/radius")
async def get_sightings_by_radius(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_m: int = Query(..., description="Radius in meters"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sightings within a radius of a location"""
    service = SightingService(db)
    sightings = service.get_sightings_by_radius(lat, lon, radius_m, current_user.org_id)
    return sightings


@router.get("/sightings/statistics")
async def get_sightings_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get sightings statistics"""
    service = SightingService(db)
    return service.get_statistics()


@router.get("/sightings/autocomplete/{field}")
async def get_autocomplete_suggestions(
    field: str,
    q: str = Query(..., description="Query string"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get autocomplete suggestions for a field"""
    service = SightingService(db)
    suggestions = service.get_autocomplete_suggestions(field, q, limit)
    return {"suggestions": suggestions}


# Status code -> RING (Vogelwarte) status text mapping for the export.
# MG = Mausergast, BV = Brutvogel; everything else / empty is unknown.
_RING_STATUS_MAP = {
    "MG": "in Mausertrupp",
    "BV": "nestbauend oder brütend",
}

# pair (Familien Status) code -> label, matching the Vogelring form dropdown.
_PAIR_LABELS = {
    "x": "Verpaart",
    "F": "Familie",
    "S": "Schule",
}

# Vogelring fields with no dedicated RING column, bundled into the RING
# "Bemerkungen" field. (label, accessor) — only filled values are emitted.
# Order follows Ingo's example; tweak once he sends the final field order.
_BEMERKUNGEN_FIELDS: list[tuple[str, "callable"]] = [
    ("Familien Status", lambda s: _PAIR_LABELS.get(s.pair, s.pair) if s.pair else None),
    ("Partner", lambda s: s.partner),
    ("Nicht flügge Junge", lambda s: s.breed_size),
    ("Flügge Junge", lambda s: s.family_size),
    ("Kleingruppe", lambda s: s.small_group_size),
    ("Großgruppe", lambda s: s.large_group_size),
    ("Habitat", lambda s: s.habitat),
    ("Kleinfläche", lambda s: s.area),
    ("Feldfrucht", lambda s: s.field_fruit),
]


def _build_bemerkungen(s: SightingDB) -> str:
    """Concatenate the filled non-RING Vogelring fields into one RING remarks string.

    Example: "Familien Status: Familie / Partner: 281937 / Nicht flügge Junge: 8".
    Empty/None fields are skipped entirely.
    """
    parts = []
    for label, accessor in _BEMERKUNGEN_FIELDS:
        value = accessor(s)
        if value is None:
            continue
        text = str(value).strip()
        if text == "":
            continue
        parts.append(f"{label}: {text}")
    return " / ".join(parts)


@router.get("/sightings/export/vogelwarte")
async def export_sightings_vogelwarte(
    start_date: DateType = Query(
        DateType(2026, 1, 1),
        description="Only Wiederfunde on/after this date (default 2026-01-01)",
    ),
    end_date: DateType | None = Query(
        None,
        description="Only Wiederfunde on/before this date (optional, no upper bound)",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export Wiederfunde (sightings) as an Excel file for the Vogelwarte RING import.

    Includes all sightings between ``start_date`` and ``end_date`` (inclusive) that
    are NOT yet marked as "gemeldet" (melded is False or NULL). Each Vogelring place
    is matched to its RING place name + coordinates via the baked-in ring_places
    lookup (blank when unmatched). Non-RING Vogelring fields are bundled into a
    "Bemerkungen" column. The melded flag is NOT modified by this export.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise HTTPException(
            status_code=500,
            detail="Excel export dependency (openpyxl) is not installed",
        ) from exc

    query = db.query(SightingDB).filter(
        SightingDB.org_id == current_user.org_id,
        SightingDB.date >= start_date,
        SightingDB.melded.isnot(True),  # False or NULL: not yet reported
    )
    if end_date is not None:
        query = query.filter(SightingDB.date <= end_date)
    sightings = query.order_by(
        SightingDB.date.asc(), SightingDB.place.asc()
    ).all()

    headers = [
        "Datum",
        "Ort",
        "RING-Ort",
        "Lat",
        "Lon",
        "Ring",
        "Spezies",
        "Alter",
        "Geschlecht",
        "Status",
        "Melder",
        "Bemerkungen",
        "Kommentar",
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Wiederfunde"
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for s in sightings:
        # Match the Vogelring place to its RING place + coordinates (blank if unmatched).
        ring_place = lookup_place(s.place)
        ws.append(
            [
                s.date.strftime("%d.%m.%Y") if s.date else "",
                s.place or "",
                ring_place.ring_place if ring_place else "",
                ring_place.lat if ring_place else "",
                ring_place.lon if ring_place else "",
                s.ring or "",
                s.species or "",
                # Age code -> RING "<code> <label>" (empty -> "2 Fängling")
                ring_age_label(s.age),
                # Sex code -> RING German text (empty -> "unbekannt")
                ring_sex_label(s.sex),
                _RING_STATUS_MAP.get(
                    (s.status or "").strip().upper(), "unbekannt / nicht erfasst"
                ),
                s.melder or "",
                # Non-RING Vogelring fields bundled into the RING remarks field.
                _build_bemerkungen(s),
                s.comment or "",
            ]
        )

    # Reasonable default column widths for readability.
    widths = [12, 28, 30, 10, 10, 16, 22, 16, 12, 24, 20, 44, 40]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + idx)].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"vogelring_wiederfunde_{DateType.today().isoformat()}.xlsx"
    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sightings/{id}")
async def get_sighting_by_id(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific sighting by ID"""
    service = SightingService(db)
    sighting = service.get_sighting_by_id(id, current_user.org_id)
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")
    return sighting


@router.get("/sightings")
async def get_sightings(
    start_date: DateType | None = Query(None, description="Start date filter"),
    end_date: DateType | None = Query(None, description="End date filter"),
    species: str | None = Query(None, description="Species filter"),
    place: str | None = Query(None, description="Place filter"),
    ring: str | None = Query(None, description="Ring filter"),
    enriched: bool = Query(False, description="Include ringing data"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all sightings with optional filters. Pagination is handled client-side."""
    service = SightingService(db)

    # Build filters
    filters = {}
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if species:
        filters["species"] = species
    if place:
        filters["place"] = place
    if ring:
        filters["ring"] = ring

    # Get sightings
    if filters:
        sightings = service.search_sightings(filters, current_user.org_id)
    elif enriched:
        sightings = service.get_enriched_sightings(current_user.org_id)
    else:
        sightings = service.get_sightings(current_user.org_id)

    return sightings


@router.post("/sightings")
async def add_sighting(
    sighting_data: SightingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new sighting"""
    service = SightingService(db)
    try:
        sighting = service.add_sighting(
            current_user.org_id, sighting_data.model_dump(exclude_unset=True)
        )
        return sighting
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sightings")
async def update_sighting(
    sighting_data: SightingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing sighting"""
    service = SightingService(db)
    try:
        sighting_id = sighting_data.id
        update_data = sighting_data.model_dump(exclude={"id"}, exclude_unset=True)
        sighting = service.update_sighting(
            sighting_id, current_user.org_id, update_data
        )
        if not sighting:
            raise HTTPException(status_code=404, detail="Sighting not found")
        return sighting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sightings/{id}")
async def delete_sighting(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a sighting"""
    service = SightingService(db)
    try:
        success = service.delete_sighting(id, current_user.org_id)
        if not success:
            raise HTTPException(status_code=404, detail="Sighting not found")
        return {"message": "Sighting deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
