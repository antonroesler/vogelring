"""
Color rings (Farbringe) API router
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...database.user_models import User
from ...utils.auth import get_current_user
from ..services.color_ring_service import ColorRingConflict, ColorRingService

router = APIRouter()


class ColorRingCreate(BaseModel):
    ring: str | None = None
    ring_color: str
    text_color: str | None = None
    code: str
    mark_type: str | None = None
    leg: str | None = None
    project: str | None = None
    comment: str | None = None


class ColorRingUpdate(BaseModel):
    ring: str | None = None
    ring_color: str | None = None
    text_color: str | None = None
    code: str | None = None
    mark_type: str | None = None
    leg: str | None = None
    project: str | None = None
    comment: str | None = None


def _raise_for(e: ValueError):
    status = 409 if isinstance(e, ColorRingConflict) else 400
    raise HTTPException(status_code=status, detail=str(e))


@router.get("/color-rings")
async def list_color_rings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ColorRingService(db)
    return [cr.to_dict() for cr in service.list_color_rings(current_user.org_id)]


@router.post("/color-rings")
async def create_color_ring(
    data: ColorRingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ColorRingService(db)
    try:
        return service.create_color_ring(current_user.org_id, data.model_dump()).to_dict()
    except ValueError as e:
        _raise_for(e)


@router.put("/color-rings/{color_ring_id}")
async def update_color_ring(
    color_ring_id: str,
    data: ColorRingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ColorRingService(db)
    try:
        color_ring = service.update_color_ring(
            color_ring_id, current_user.org_id, data.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        _raise_for(e)
    if not color_ring:
        raise HTTPException(status_code=404, detail="Farbring nicht gefunden")
    return color_ring.to_dict()


@router.delete("/color-rings/{color_ring_id}")
async def delete_color_ring(
    color_ring_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ColorRingService(db)
    if not service.delete_color_ring(color_ring_id, current_user.org_id):
        raise HTTPException(status_code=404, detail="Farbring nicht gefunden")
    return {"message": "Farbring gelöscht"}
