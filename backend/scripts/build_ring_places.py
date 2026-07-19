#!/usr/bin/env python3
"""Build the RING place lookup (``src/data/ring_places.json``) from Ingo's RING
geo-table export.

Ingo maintains the mapping in an Excel export of RING's ``tblGeoTab``:
    A idGeoTab | B lngLong | C lngLat | D strPlace (RING name) | E OrtVogelring | F date

Column E holds the Vogelring place name for the rows he has matched. This script
extracts the matched rows into a JSON lookup keyed by the (normalized) Vogelring
place name, so the Wiederfunde export can attach the RING place name + coordinates.

Usage:
    uv run python scripts/build_ring_places.py "/path/to/Kopie von tblGeoTab2025_02.xlsx"

Re-run whenever Ingo sends an updated table, then commit the regenerated JSON.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import openpyxl

OUT_PATH = Path(__file__).resolve().parent.parent / "src" / "data" / "ring_places.json"


def normalize(name: str) -> str:
    """Normalize a place name for matching (collapse whitespace, casefold)."""
    return " ".join(str(name).split()).casefold()


def build(xlsx_path: str) -> dict:
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active

    entries: dict[str, dict] = {}
    skipped = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        # idGeoTab, lngLong, lngLat, strPlace, OrtVogelring, date
        lng, lat, ring_place, vogelring_name = row[1], row[2], row[3], row[4]
        if vogelring_name in (None, "") or str(vogelring_name).strip() == "":
            continue
        key = normalize(vogelring_name)
        if lat is None or lng is None:
            skipped += 1
            continue
        entries[key] = {
            "vogelring_place": str(vogelring_name).strip(),
            "ring_place": str(ring_place).strip() if ring_place else "",
            "lat": float(lat),
            "lon": float(lng),
        }
    return entries


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    entries = build(sys.argv[1])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(entries)} place mappings to {OUT_PATH}")


if __name__ == "__main__":
    main()
