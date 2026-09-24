"""
Sightings API router
"""

import io
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session
from datetime import date as DateType, datetime as DateTimeType, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel

from ...utils.auth import get_current_user
from ...database.connection import get_db
from ...database.user_models import User
from ...database.models import Sighting as SightingDB
from ...database.models import SightingExport as SightingExportDB
from ...database.models import SightingExportItem as SightingExportItemDB
from ...utils.sighting_coding import ring_age_label, ring_sex_label
from ...utils.ring_places import lookup_place, smart_match_place
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
    return service.get_statistics(current_user.org_id)


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
    suggestions = service.get_autocomplete_suggestions(
        current_user.org_id, field, q, limit
    )
    return {"suggestions": suggestions}


# Status code -> RING (Vogelwarte) status text mapping for the export.
# Only these two Vogelring statuses carry over to the RING Status field.
# MG = Mausergast, BV = Brutvogel; everything else / empty is left blank.
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


def _melder_for_bemerkungen(s: SightingDB):
    """Melder for the Bemerkungen field — omitted when it's IR (the default enterer)."""
    m = (s.melder or "").strip()
    if not m or m.upper() == "IR":
        return None
    return m


# Vogelring fields with no dedicated RING column, bundled into the RING
# "Bemerkungen" field. (label, accessor) — only filled values are emitted, in
# Ingo's specified order. Melder + Kommentar are NOT separate RING columns, so
# they live here too; Habitat/Kleinfläche are intentionally left out.
_BEMERKUNGEN_FIELDS: list[tuple[str, "callable"]] = [
    ("Melder", _melder_for_bemerkungen),
    ("Großgruppe", lambda s: s.large_group_size),
    ("Kleingruppe", lambda s: s.small_group_size),
    ("Familien Status", lambda s: _PAIR_LABELS.get(s.pair, s.pair) if s.pair else None),
    ("Partner", lambda s: s.partner),
    ("Nicht flügge Junge", lambda s: s.breed_size),
    ("Flügge Junge", lambda s: s.family_size),
    ("Feldfrucht", lambda s: s.field_fruit),
    ("Kommentare", lambda s: s.comment),
]


def _ring_place_columns(s: SightingDB) -> tuple[str, object, object]:
    """Return (RING-Ort, Lat, Lon) for a sighting.

    Prefer Ingo's explicit mapping; otherwise fall back to the GPS-nearest RING
    place (within 500 m + name overlap), flagged "(auto)" so it's clearly an
    unverified suggestion. Blank when neither resolves.
    """
    explicit = lookup_place(s.place)
    if explicit is not None:
        return explicit.ring_place, explicit.lat, explicit.lon
    auto = smart_match_place(s.place, s.lat, s.lon)
    if auto is not None:
        return f"{auto.ring_place} (auto)", auto.lat, auto.lon
    return "", "", ""


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


def _utcnow() -> DateTimeType:
    """Naive UTC, matching how the DB's own CURRENT_TIMESTAMP columns are stored.

    ``datetime.now()`` would follow the container's local timezone and silently
    skew these timestamps against every other created_at in the schema.
    """
    return DateTimeType.now(timezone.utc).replace(tzinfo=None)


def _unreported_sightings_query(
    db: Session,
    org_id,
    start_date: DateType,
    end_date: DateType | None,
    created_before: DateTimeType | None = None,
):
    """The exact set the Wiederfunde export ships: not-yet-reported sightings in range.

    ``created_before`` additionally excludes sightings entered after a given moment
    — used when reconstructing an export that was taken in the past, so entries
    added since then don't get swept in.
    """
    query = db.query(SightingDB).filter(
        SightingDB.org_id == org_id,
        SightingDB.date >= start_date,
        SightingDB.melded.isnot(True),  # False or NULL: not yet reported
    )
    if end_date is not None:
        query = query.filter(SightingDB.date <= end_date)
    if created_before is not None:
        query = query.filter(SightingDB.created_at <= created_before)
    return query


def _record_export_run(
    db: Session,
    org_id,
    sightings: list[SightingDB],
    start_date: DateType,
    end_date: DateType | None,
    filename: str | None,
    source: str = "export",
    note: str | None = None,
) -> SightingExportDB:
    """Persist which sightings went into one export, so they can be marked later."""
    run = SightingExportDB(
        id=uuid4(),
        org_id=org_id,
        # Set explicitly rather than via the server default: SQLite's
        # CURRENT_TIMESTAMP is only second-granular, which would make two exports
        # in the same second sort unpredictably in the history list.
        created_at=_utcnow(),
        start_date=start_date,
        end_date=end_date,
        row_count=len(sightings),
        filename=filename,
        source=source,
        note=note,
    )
    db.add(run)
    db.flush()
    for s in sightings:
        db.add(SightingExportItemDB(export_id=run.id, sighting_id=s.id))
    db.commit()
    db.refresh(run)
    return run


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
    is matched to its RING place name + coordinates: Ingo's explicit map first, else
    the GPS-nearest RING place within 500 m whose name overlaps (flagged "(auto)"),
    else blank. Non-RING Vogelring fields are bundled into a "Bemerkungen" column.

    The melded flag is NOT modified here — the Vogelwarte only accepts a delivery
    days later. Instead the run is recorded (see ``GET /sightings/exports``) so the
    exact set can be bulk-marked as gemeldet once the delivery is confirmed.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise HTTPException(
            status_code=500,
            detail="Excel export dependency (openpyxl) is not installed",
        ) from exc

    sightings = (
        _unreported_sightings_query(db, current_user.org_id, start_date, end_date)
        .order_by(SightingDB.date.asc(), SightingDB.place.asc())
        .all()
    )

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
        "Bemerkungen",
    ]

    wb = Workbook()
    ws = wb.active
    ws.title = "Wiederfunde"
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for s in sightings:
        # Match the Vogelring place to its RING place + coordinates (explicit map,
        # else GPS-nearest "(auto)" suggestion, else blank).
        ring_ort, ring_lat, ring_lon = _ring_place_columns(s)
        ws.append(
            [
                s.date.strftime("%d.%m.%Y") if s.date else "",
                s.place or "",
                ring_ort,
                ring_lat,
                ring_lon,
                s.ring or "",
                s.species or "",
                # Age code -> RING "<code> <label>" (empty -> "2 Fängling")
                ring_age_label(s.age),
                # Sex code -> RING German text (empty -> "unbekannt")
                ring_sex_label(s.sex),
                _RING_STATUS_MAP.get((s.status or "").strip().upper(), ""),
                # Non-RING Vogelring fields (incl. Melder + Kommentar) bundled here.
                _build_bemerkungen(s),
            ]
        )

    # Reasonable default column widths for readability.
    widths = [12, 28, 30, 10, 10, 16, 22, 16, 12, 24, 60]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + idx)].width = width

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"vogelring_wiederfunde_{DateType.today().isoformat()}.xlsx"

    # Remember what went out, so it can be marked gemeldet once the Vogelwarte
    # accepts it. An empty export has nothing to mark — don't clutter the list.
    if sightings:
        _record_export_run(
            db,
            current_user.org_id,
            sightings,
            start_date,
            end_date,
            filename,
        )

    return StreamingResponse(
        buffer,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class ExportRunOut(BaseModel):
    """One recorded export run, plus how much of it is still unreported."""

    id: str
    created_at: DateTimeType | None = None
    start_date: DateType | None = None
    end_date: DateType | None = None
    row_count: int
    filename: str | None = None
    source: str
    note: str | None = None
    marked_melded_at: DateTimeType | None = None
    marked_count: int | None = None
    # Sightings from this run that are still not gemeldet — what a mark would flip.
    pending_count: int


class ExportBackfillRequest(BaseModel):
    """Reconstruct an export that was delivered before runs were recorded."""

    start_date: DateType
    end_date: DateType | None = None
    # Optional cut-off: ignore sightings entered after the export was taken.
    created_before: DateTimeType | None = None
    note: str | None = None
    # Preview only — nothing is written and nothing is marked.
    dry_run: bool = True


# Postgres caps bind parameters per statement; chunk large id lists.
_ID_CHUNK = 500


def _chunks(values: list, size: int = _ID_CHUNK):
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _pending_counts(db: Session, run_ids: list) -> dict:
    """For each run id: how many of its sightings are still not gemeldet."""
    counts: dict = {}
    for chunk in _chunks(run_ids):
        rows = (
            db.query(SightingExportItemDB.export_id, sa_func.count())
            .join(SightingDB, SightingDB.id == SightingExportItemDB.sighting_id)
            .filter(
                SightingExportItemDB.export_id.in_(chunk),
                SightingDB.melded.isnot(True),
            )
            .group_by(SightingExportItemDB.export_id)
            .all()
        )
        for export_id, count in rows:
            counts[export_id] = count
    return counts


def _run_out(run: SightingExportDB, pending: int) -> ExportRunOut:
    return ExportRunOut(
        id=str(run.id),
        created_at=run.created_at,
        start_date=run.start_date,
        end_date=run.end_date,
        row_count=run.row_count,
        filename=run.filename,
        source=run.source,
        note=run.note,
        marked_melded_at=run.marked_melded_at,
        marked_count=run.marked_count,
        pending_count=pending,
    )


def _get_run(db: Session, export_id: str, org_id) -> SightingExportDB:
    try:
        run_uuid = UUID(export_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Export not found")
    run = (
        db.query(SightingExportDB)
        .filter(SightingExportDB.id == run_uuid, SightingExportDB.org_id == org_id)
        .first()
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Export not found")
    return run


@router.get("/sightings/exports")
async def list_sighting_exports(
    limit: int = Query(20, ge=1, le=100, description="How many runs to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recent Wiederfunde export runs, newest first."""
    runs = (
        db.query(SightingExportDB)
        .filter(SightingExportDB.org_id == current_user.org_id)
        .order_by(SightingExportDB.created_at.desc(), SightingExportDB.id.desc())
        .limit(limit)
        .all()
    )
    pending = _pending_counts(db, [r.id for r in runs])
    return [_run_out(r, pending.get(r.id, 0)) for r in runs]


@router.get("/sightings/exports/{export_id}/sightings")
async def get_sighting_export_items(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The sightings contained in one export run, with their current melded state."""
    run = _get_run(db, export_id, current_user.org_id)
    rows = (
        db.query(SightingDB)
        .join(
            SightingExportItemDB,
            SightingExportItemDB.sighting_id == SightingDB.id,
        )
        .filter(SightingExportItemDB.export_id == run.id)
        .order_by(SightingDB.date.asc(), SightingDB.place.asc())
        .all()
    )
    return [
        {
            "id": str(s.id),
            "date": s.date,
            "ring": s.ring,
            "species": s.species,
            "place": s.place,
            "melder": s.melder,
            "melded": bool(s.melded),
        }
        for s in rows
    ]


@router.post("/sightings/exports/{export_id}/mark-melded")
async def mark_export_melded(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark every sighting of this export run as gemeldet.

    Only flips sightings that are not already gemeldet, and remembers exactly which
    ones it flipped so the run can be undone. Safe to call twice.
    """
    run = _get_run(db, export_id, current_user.org_id)

    pending_ids = [
        row[0]
        for row in db.query(SightingDB.id)
        .join(
            SightingExportItemDB,
            SightingExportItemDB.sighting_id == SightingDB.id,
        )
        .filter(
            SightingExportItemDB.export_id == run.id,
            SightingDB.org_id == current_user.org_id,
            SightingDB.melded.isnot(True),
        )
        .all()
    ]

    for chunk in _chunks(pending_ids):
        db.query(SightingDB).filter(
            SightingDB.org_id == current_user.org_id,
            SightingDB.id.in_(chunk),
        ).update({SightingDB.melded: True}, synchronize_session=False)
        db.query(SightingExportItemDB).filter(
            SightingExportItemDB.export_id == run.id,
            SightingExportItemDB.sighting_id.in_(chunk),
        ).update({SightingExportItemDB.marked_melded: True}, synchronize_session=False)

    run.marked_melded_at = _utcnow()
    run.marked_count = (run.marked_count or 0) + len(pending_ids)
    db.commit()
    db.refresh(run)

    return {
        "marked": len(pending_ids),
        "already_melded": run.row_count - len(pending_ids),
        "total": run.row_count,
        "run": _run_out(run, 0),
    }


@router.post("/sightings/exports/{export_id}/unmark-melded")
async def unmark_export_melded(
    export_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Undo this run's bulk-mark.

    Resets only the sightings this run actually flipped — anything that was already
    gemeldet before the run, or marked by a different run, stays untouched.
    """
    run = _get_run(db, export_id, current_user.org_id)

    marked_ids = [
        row[0]
        for row in db.query(SightingExportItemDB.sighting_id)
        .filter(
            SightingExportItemDB.export_id == run.id,
            SightingExportItemDB.marked_melded.is_(True),
        )
        .all()
    ]

    for chunk in _chunks(marked_ids):
        db.query(SightingDB).filter(
            SightingDB.org_id == current_user.org_id,
            SightingDB.id.in_(chunk),
        ).update({SightingDB.melded: False}, synchronize_session=False)
        db.query(SightingExportItemDB).filter(
            SightingExportItemDB.export_id == run.id,
            SightingExportItemDB.sighting_id.in_(chunk),
        ).update({SightingExportItemDB.marked_melded: False}, synchronize_session=False)

    run.marked_melded_at = None
    run.marked_count = None
    db.commit()
    db.refresh(run)

    pending = _pending_counts(db, [run.id]).get(run.id, 0)
    return {"unmarked": len(marked_ids), "run": _run_out(run, pending)}


@router.post("/sightings/exports/backfill")
async def backfill_sighting_export(
    payload: ExportBackfillRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record an export that was already delivered, and mark its sightings gemeldet.

    Reconstructs the set the export would have contained (unreported sightings in
    the range, optionally limited to those entered before ``created_before``).
    With ``dry_run`` (the default) nothing is written — it only reports what would
    be affected, so the range can be verified before any data changes.
    """
    sightings = (
        _unreported_sightings_query(
            db,
            current_user.org_id,
            payload.start_date,
            payload.end_date,
            payload.created_before,
        )
        .order_by(SightingDB.date.asc(), SightingDB.place.asc())
        .all()
    )

    preview = [
        {
            "id": str(s.id),
            "date": s.date,
            "ring": s.ring,
            "species": s.species,
            "place": s.place,
        }
        for s in sightings[:20]
    ]

    if payload.dry_run:
        return {
            "dry_run": True,
            "matched": len(sightings),
            "preview": preview,
            "run": None,
        }

    if not sightings:
        raise HTTPException(
            status_code=400,
            detail="Keine nicht gemeldeten Einträge in diesem Zeitraum",
        )

    # Read the ids up front: recording the run commits, which expires the loaded
    # instances — touching them afterwards would re-select every single row.
    ids = [s.id for s in sightings]

    run = _record_export_run(
        db,
        current_user.org_id,
        sightings,
        payload.start_date,
        payload.end_date,
        filename=None,
        source="manual",
        note=payload.note,
    )

    for chunk in _chunks(ids):
        db.query(SightingDB).filter(
            SightingDB.org_id == current_user.org_id,
            SightingDB.id.in_(chunk),
        ).update({SightingDB.melded: True}, synchronize_session=False)
        db.query(SightingExportItemDB).filter(
            SightingExportItemDB.export_id == run.id,
            SightingExportItemDB.sighting_id.in_(chunk),
        ).update({SightingExportItemDB.marked_melded: True}, synchronize_session=False)

    run.marked_melded_at = _utcnow()
    run.marked_count = len(ids)
    db.commit()
    db.refresh(run)

    return {
        "dry_run": False,
        "matched": len(sightings),
        "marked": len(ids),
        "preview": preview,
        "run": _run_out(run, 0),
    }


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
