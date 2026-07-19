#!/usr/bin/env python3
"""Build the RING place lookup (``src/data/ring_places.json``) from Ingo's RING
geo-table export.

Ingo maintains the mapping in an Excel export of RING's ``tblGeoTab``:
    A idGeoTab | B lngLong | C lngLat | D strPlace (RING name) | E OrtVogelring | F date

Column E holds the Vogelring place name for the rows he has matched. This script
writes TWO files:
  - ``ring_places.json`` — the explicit col-E map (Vogelring name -> RING place +
    coords). Authoritative, curated by Ingo.
  - ``ring_geo.json``    — EVERY RING place with coordinates, for the "smart"
    GPS-nearest fallback (match a sighting's own coordinates to the closest RING
    place when Ingo hasn't linked the place name yet).

Usage:
    uv run python scripts/build_ring_places.py "/path/to/Kopie von tblGeoTab2025_02.xlsx"

Re-run whenever Ingo sends an updated table, then commit the regenerated JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "data"
OUT_PATH = DATA_DIR / "ring_places.json"
GEO_PATH = DATA_DIR / "ring_geo.json"


def normalize(name: str) -> str:
    """Normalize a place name for matching (collapse whitespace, casefold)."""
    return " ".join(str(name).split()).casefold()


def build(xlsx_path: str) -> tuple[dict, list]:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    entries: dict[str, dict] = {}
    geo: list[dict] = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        # idGeoTab, lngLong, lngLat, strPlace, OrtVogelring, date
        lng, lat, ring_place, vogelring_name = row[1], row[2], row[3], row[4]
        if lat is None or lng is None:
            continue
        ring_place_str = str(ring_place).strip() if ring_place else ""

        # Every RING place with coords feeds the GPS-nearest fallback.
        if ring_place_str:
            geo.append(
                {"ring_place": ring_place_str, "lat": float(lat), "lon": float(lng)}
            )

        # Explicit col-E mapping (Ingo-curated).
        if vogelring_name not in (None, "") and str(vogelring_name).strip() != "":
            entries[normalize(vogelring_name)] = {
                "vogelring_place": str(vogelring_name).strip(),
                "ring_place": ring_place_str,
                "lat": float(lat),
                "lon": float(lng),
            }
    return entries, geo


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    entries, geo = build(sys.argv[1])
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    geo.sort(key=lambda g: g["ring_place"])
    GEO_PATH.write_text(
        json.dumps(geo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} explicit mappings to {OUT_PATH}")
    print(f"Wrote {len(geo)} RING geo places to {GEO_PATH}")


if __name__ == "__main__":
    main()
