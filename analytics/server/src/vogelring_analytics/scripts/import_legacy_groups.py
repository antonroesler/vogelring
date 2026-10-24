"""Port the old Streamlit app's „Datasets“ (JSON files) into Gruppen of the analytics catalog.

    uv run python -m vogelring_analytics.scripts.import_legacy_groups /data/legacy_datasets

Idempotent: ids derive from the legacy name, so re-running updates instead of duplicating. Every filter that has no
exact counterpart is reported (never silently dropped). Writes only to the analytics catalog, never to Vogelring.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .. import engine


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    directory = Path(args[0]) if args else Path(__file__).resolve().parents[3] / "legacy" / "datasets"
    try:
        out = engine.import_legacy_groups(directory, by="import")
    except engine.EngineError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    for r in out["items"]:
        if r["status"] == "error":
            print(f"✗ {r['file']}: {r['error']}")
            continue
        flag = " (leer!)" if r.get("empty") else ""
        print(f"{'+' if r['status'] == 'created' else '~'} {r['name']}  [{r['group_id']}]{flag}\n    {r['describe']}")
        for n in r.get("notes") or []:
            print(f"    ! {n}")
    print(f"{out['count']} Gruppen verarbeitet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
