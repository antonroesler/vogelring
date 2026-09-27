"""
Color ring (Farbring) service: registry maintenance and sighting resolution
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...database.models import ColorRing
from ...database.repositories import ColorRingRepository
from ...utils.color_rings import (
    LEGS,
    MARK_TYPES,
    color_label,
    normalize_code,
    validate_color,
)

logger = logging.getLogger(__name__)

SIGHTING_FIELDS = ("color_ring_color", "color_ring_text_color", "color_ring_code")


class ColorRingConflict(ValueError):
    """The color ring or metal ring is already taken by another bird"""


def describe(color_ring: ColorRing) -> str:
    text = f" / {color_label(color_ring.text_color)}" if color_ring.text_color else ""
    return f"{color_label(color_ring.ring_color)}{text} {color_ring.code}"


class ColorRingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ColorRingRepository(db)

    def list_color_rings(self, org_id: str) -> List[ColorRing]:
        return self.repository.get_all(org_id)

    def get_color_ring(self, color_ring_id: str, org_id: str) -> Optional[ColorRing]:
        return self.repository.get_by_id(color_ring_id, org_id)

    def get_by_ring(self, ring: str, org_id: str) -> Optional[ColorRing]:
        return self.repository.get_by_ring(ring, org_id)

    def create_color_ring(self, org_id: str, data: Dict[str, Any]) -> ColorRing:
        values = self._clean(data)
        self._check_conflicts(org_id, values)
        try:
            color_ring = self.repository.create(org_id, **values)
        except IntegrityError as e:
            raise ColorRingConflict("Dieser Farbring ist bereits vergeben") from e
        self.repository.backfill_sighting_rings(color_ring)
        return color_ring

    def update_color_ring(
        self, color_ring_id: str, org_id: str, data: Dict[str, Any]
    ) -> Optional[ColorRing]:
        existing = self.repository.get_by_id(color_ring_id, org_id)
        if not existing:
            return None
        merged = existing.to_dict() | data
        values = self._clean(merged)
        self._check_conflicts(org_id, values, exclude_id=existing.id)
        try:
            color_ring = self.repository.update(color_ring_id, org_id, **values)
        except IntegrityError as e:
            raise ColorRingConflict("Dieser Farbring ist bereits vergeben") from e
        self.repository.backfill_sighting_rings(color_ring)
        return color_ring

    def delete_color_ring(self, color_ring_id: str, org_id: str) -> bool:
        return self.repository.delete(color_ring_id, org_id)

    def resolve_sighting(
        self, org_id: str, data: Dict[str, Any], existing: Any = None
    ) -> Dict[str, Any]:
        """Normalize a sighting's color ring fields and link it to the registry.

        - A known color ring fills in the metal ring when it was left empty.
        - A known color ring without metal ring gets linked to the sighting's ring.
        - An unknown color ring is added to the registry.
        Ambiguous matches (text color unknown, several candidates) are left alone.
        """
        for key in SIGHTING_FIELDS:
            if key in data:
                data[key] = data[key] or None
        if "color_ring_color" in data:
            data["color_ring_color"] = validate_color(data["color_ring_color"], "Farbring")
        if "color_ring_text_color" in data:
            data["color_ring_text_color"] = validate_color(
                data["color_ring_text_color"], "Schriftfarbe"
            )
        if "color_ring_code" in data:
            data["color_ring_code"] = normalize_code(data["color_ring_code"])

        def effective(key: str):
            if key in data:
                return data[key]
            return getattr(existing, key, None) if existing is not None else None

        color = effective("color_ring_color")
        text_color = effective("color_ring_text_color")
        code = effective("color_ring_code")
        ring = effective("ring")

        if not color and not code and not text_color:
            return data
        if not color or not code:
            raise ValueError("Farbring unvollständig: Ringfarbe und Code angeben")

        candidates = self.repository.find_by_identity(org_id, color, code, text_color)
        if len(candidates) > 1:
            return data

        ring_owner = self.repository.get_by_ring(ring, org_id) if ring else None

        if not candidates:
            self.repository.create(
                org_id,
                ring=ring if ring and not ring_owner else None,
                ring_color=color,
                text_color=text_color,
                code=code,
            )
            return data

        color_ring = candidates[0]
        if color_ring.ring and not ring:
            data["ring"] = color_ring.ring
        elif not color_ring.ring and ring and not ring_owner:
            color_ring.ring = ring
            self.db.commit()
            self.repository.backfill_sighting_rings(color_ring)
        return data

    def _clean(self, data: Dict[str, Any]) -> Dict[str, Any]:
        ring_color = validate_color(data.get("ring_color"), "Ringfarbe")
        code = normalize_code(data.get("code"))
        if not ring_color or not code:
            raise ValueError("Farbring braucht Ringfarbe und Code")
        mark_type = data.get("mark_type") or None
        if mark_type and mark_type not in MARK_TYPES:
            raise ValueError(f"Unbekannte Markierungsart: {mark_type}")
        leg = data.get("leg") or None
        if leg and leg not in LEGS:
            raise ValueError(f"Unbekanntes Bein: {leg}")
        return {
            "ring": (data.get("ring") or "").strip() or None,
            "ring_color": ring_color,
            "text_color": validate_color(data.get("text_color"), "Schriftfarbe"),
            "code": code,
            "mark_type": mark_type,
            "leg": leg,
            "project": (data.get("project") or "").strip() or None,
            "comment": (data.get("comment") or "").strip() or None,
        }

    def _check_conflicts(
        self, org_id: str, values: Dict[str, Any], exclude_id: Any = None
    ) -> None:
        if values["ring"]:
            owner = self.repository.get_by_ring(values["ring"], org_id)
            if owner and owner.id != exclude_id:
                raise ColorRingConflict(
                    f"Ring {values['ring']} hat bereits den Farbring {describe(owner)}"
                )
        for other in self.repository.find_by_identity(
            org_id, values["ring_color"], values["code"], values["text_color"]
        ):
            if other.id == exclude_id or other.text_color != values["text_color"]:
                continue
            owner = f" (Ring {other.ring})" if other.ring else ""
            raise ColorRingConflict(
                f"Farbring {describe(other)} ist bereits vergeben{owner}"
            )
