from __future__ import annotations

import argparse
import csv
import pickle
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def ensure_api_on_syspath() -> None:
    """Ensure `ring-api/src` is on sys.path so pickled models can be imported.

    Unpickling `Sighting` objects requires the class to be importable at
    `api.models.sightings.Sighting` (and its enums). We add that path explicitly
    relative to this repository layout.
    """
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent  # vogelring/
    api_src = repo_root / "ring-api" / "src"
    if str(api_src) not in sys.path:
        sys.path.insert(0, str(api_src))


ensure_api_on_syspath()

# Import after sys.path adjustment so pickle can resolve classes
from api.models.sightings import Sighting  # type: ignore  # noqa: E402
from api.models.ringing import Ringing  # type: ignore  # noqa: E402


def load_pickled_sightings(file_path: Path) -> List[Sighting]:
    with open(file_path, "rb") as f:
        data = pickle.load(f)
    # Accept either a single Sighting or a list of them
    if isinstance(data, Sighting):
        return [data]
    return list(data)


def iter_sightings(inputs: Iterable[Path]) -> Iterable[Sighting]:
    for input_path in inputs:
        if input_path.is_dir():
            for pkl in sorted(input_path.glob("**/*.pkl")):
                yield from load_pickled_sightings(pkl)
        else:
            yield from load_pickled_sightings(input_path)


CSV_FIELDS: list[str] = [
    "id",
    "excel_id",
    "species",
    "ring",
    "reading",
    "date",
    "place",
    "area",
    "sex",
    "age",
    "breed_size",
    "family_size",
    "pair",
    "small_group_size",
    "large_group_size",
    "partner",
    "status",
    "habitat",
    "field_fruit",
    "comment",
    "melder",
    "melded",
    "lat",
    "lon",
    "is_exact_location",
]

# Ringing fields to join into the CSV
RINGING_FIELDS: list[str] = [
    "ringing_ring_scheme",
    "ringing_species",
    "ringing_date",
    "ringing_place",
    "ringing_lat",
    "ringing_lon",
    "ringing_ringer",
    "ringing_sex",
    "ringing_age",
    "ringing_status",
]

# Always include ringing columns for a consistent schema
CSV_FIELDS = CSV_FIELDS + RINGING_FIELDS


def sighting_to_row(s: Sighting, ringing_map: Optional[Dict[str, Ringing]] = None) -> dict[str, str]:
    def to_str(value) -> str:
        if value is None:
            return ""
        # Enums
        if hasattr(value, "value"):
            try:
                return str(value.value)
            except Exception:
                return str(value)
        # Dates
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        # Booleans
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    data = s.model_dump() if hasattr(s, "model_dump") else s.dict()  # pydantic v2 vs v1

    row = {field: to_str(data.get(field)) for field in CSV_FIELDS}

    # Join ringing data if available
    if ringing_map and s.ring:
        r = ringing_map.get(normalize_ring(s.ring))
        if r is not None:
            rdata = r.model_dump() if hasattr(r, "model_dump") else r.dict()
            row.update(
                {
                    "ringing_ring_scheme": to_str(rdata.get("ring_scheme")),
                    "ringing_species": to_str(rdata.get("species")),
                    "ringing_date": to_str(rdata.get("date")),
                    "ringing_place": to_str(rdata.get("place")),
                    "ringing_lat": to_str(rdata.get("lat")),
                    "ringing_lon": to_str(rdata.get("lon")),
                    "ringing_ringer": to_str(rdata.get("ringer")),
                    "ringing_sex": to_str(rdata.get("sex")),
                    "ringing_age": to_str(rdata.get("age")),
                    "ringing_status": to_str(rdata.get("status")),
                }
            )

    return row


def normalize_ring(ring: str) -> str:
    return "".join(ch for ch in ring if ch.isalnum()).upper()


def load_ringings_from_csv(csv_path: Path, delimiter: str = ";", encoding: str = "utf-8") -> Dict[str, Ringing]:
    """Load ringings from a CSV that includes a header with at least a 'ring' column.

    Tries to map known columns to the Ringing model; unknown/missing fields are ignored.
    """
    with open(csv_path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames or "ring" not in [h.strip() for h in reader.fieldnames if h]:
            raise ValueError("Ringings CSV must have a header with a 'ring' column")

        mapping: Dict[str, Ringing] = {}
        for row in reader:
            ring_raw = (row.get("ring") or "").strip()
            if not ring_raw:
                continue
            try:
                ringing_kwargs = {
                    "ring": ring_raw,
                    "ring_scheme": row.get("ring_scheme"),
                    "species": row.get("species"),
                    "date": row.get("date"),  # Ringing.model_dump handles isoformat; we'll pass through as string
                    "place": row.get("place"),
                    "lat": float(row["lat"]) if row.get("lat") else None,
                    "lon": float(row["lon"]) if row.get("lon") else None,
                    "ringer": row.get("ringer"),
                    "sex": int(row["sex"]) if row.get("sex") else None,
                    "age": int(row["age"]) if row.get("age") else None,
                }
                # Drop Nones to satisfy pydantic types where needed
                ringing = Ringing(**{k: v for k, v in ringing_kwargs.items() if v is not None})
                mapping[normalize_ring(ring_raw)] = ringing
            except Exception:
                # If a row can't be parsed, skip it silently to keep export robust
                continue
        return mapping


def load_ringings_from_pkl(pkl_path: Path) -> Dict[str, Ringing]:
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    items: List[Ringing]
    if isinstance(data, Ringing):
        items = [data]
    else:
        items = list(data)
    return {normalize_ring(r.ring): r for r in items if getattr(r, "ring", None)}


def load_ringings_from_dynamo(rings: Iterable[str]) -> Dict[str, Ringing]:
    """Fetch ringings from DynamoDB for the provided rings using the project's DAO.

    Requires AWS credentials and environment/table configuration matching api.db.dynamo.
    """
    try:
        from api.db.dynamo import get_ringing_by_ring  # type: ignore
    except Exception:
        return {}

    mapping: Dict[str, Ringing] = {}
    seen: set[str] = set()
    for ring in rings:
        key = normalize_ring(ring)
        if not key or key in seen:
            continue
        seen.add(key)
        try:
            r = get_ringing_by_ring(ring)
            if r is not None:
                mapping[key] = r
        except Exception:
            # Skip failures; keep export going
            continue
    return mapping


def default_output_for_input(input_path: Path) -> Path:
    if input_path.is_dir():
        return input_path / "sightings.csv"
    return input_path.with_suffix(".csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert pickled Sighting objects to CSV")
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Path(s) to .pkl file(s) or directories containing .pkl files",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV file path. If multiple inputs are given and this is omitted, defaults to ./sightings.csv",
    )
    parser.add_argument("--delimiter", default=";", help="CSV delimiter (default: ';')")
    parser.add_argument("--encoding", default="utf-8", help="CSV encoding (default: utf-8)")
    parser.add_argument(
        "--ringings-csv", help="Optional: path to a CSV file with ringings (must include 'ring' header)"
    )
    parser.add_argument("--ringings-pkl", help="Optional: path to a pickle containing Ringing or list[Ringing]")
    parser.add_argument(
        "--ringings-dynamo",
        action="store_true",
        help="Optional: fetch ringings from DynamoDB for rings present in the input",
    )

    args = parser.parse_args()

    input_paths = [Path(p).expanduser().resolve() for p in args.inputs]
    if len(input_paths) == 1 and not args.output:
        output_path = default_output_for_input(input_paths[0]).resolve()
    else:
        output_path = Path(args.output or "sightings.csv").expanduser().resolve()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare ringing map, if any source provided
    ringing_map: Dict[str, Ringing] | None = None
    if args.ringings_csv:
        ringing_map = load_ringings_from_csv(
            Path(args.ringings_csv).expanduser().resolve(), args.delimiter, args.encoding
        )
    elif args.ringings_pkl:
        ringing_map = load_ringings_from_pkl(Path(args.ringings_pkl).expanduser().resolve())
    elif args.ringings_dynamo:
        # Collect unique rings first
        rings: list[str] = []
        for input_path in input_paths:
            # load briefly to collect rings
            if input_path.is_dir():
                for pkl in sorted(input_path.glob("**/*.pkl")):
                    for s in load_pickled_sightings(pkl):
                        if s.ring:
                            rings.append(s.ring)
            else:
                for s in load_pickled_sightings(input_path):
                    if s.ring:
                        rings.append(s.ring)
        ringing_map = load_ringings_from_dynamo(rings)

    # Stream to CSV to avoid large memory spikes
    with open(output_path, "w", newline="", encoding=args.encoding) as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_FIELDS, delimiter=args.delimiter)
        writer.writeheader()
        count = 0
        for s in iter_sightings(input_paths):
            writer.writerow(sighting_to_row(s, ringing_map))
            count += 1

    print(f"Wrote {count} sightings to {output_path}")


if __name__ == "__main__":
    main()
