import asyncio
import re
import types
from uuid import uuid4

import pytest

from vogelring_analytics import runtime, writes
from vogelring_analytics.catalog import Catalog
from vogelring_analytics.definitions import DefinitionStore
from vogelring_analytics.writes import ConvertToColorRing, MergeReadingToRing, RenamePlace, SetFields, WriteError, plan

ORG = str(uuid4())
OTHER = str(uuid4())


class FakeResult:
    def __init__(self, columns, rows):
        self.columns, self.rows, self.truncated = columns, rows, False


class FakeReadDB:
    """Minimal read-only DB: tables as list[dict]; supports the WHERE shapes used by writes._select."""

    def __init__(self, tables):
        self.tables = tables
        self.queries = []

    async def query(self, sql, *, params=None, max_rows=None):
        self.queries.append((sql, params))
        m = re.match(r"SELECT (.+?) FROM (\w+) WHERE (.+?) ORDER BY 1", sql, re.S)
        cols = [c.strip() for c in m.group(1).split(",")]
        table, where = m.group(2), m.group(3)
        params = list(params or [])
        conds = [c.strip() for c in where.split(" AND ")]
        rows = []
        for r in self.tables.get(table, []):
            ok = True
            pi = 0
            for c in conds:
                if c == "TRUE":
                    continue
                if c.startswith("(ring = %s OR reading = %s)"):
                    v1, v2 = params[pi], params[pi + 1]
                    pi += 2
                    ok &= r.get("ring") == v1 or r.get("reading") == v2
                elif c == "ring IS NULL":
                    ok &= r.get("ring") is None
                elif c == "org_id = %s::uuid":
                    ok &= str(r.get("org_id")) == params[pi]
                    pi += 1
                elif c == "COALESCE(text_color, '') = %s":
                    ok &= (r.get("text_color") or "") == params[pi]
                    pi += 1
                elif c.endswith("= ANY(%s::uuid[])"):
                    ok &= str(r.get("id")) in params[pi]
                    pi += 1
                elif c.endswith(">= %s::date") or c.endswith("<= %s::date"):
                    col = c.split()[0]
                    v = params[pi]
                    pi += 1
                    ok &= (str(r.get(col)) >= v) if ">=" in c else (str(r.get(col)) <= v)
                elif "%s" in c:
                    col = c.split()[0]
                    ok &= r.get(col) == params[pi]
                    pi += 1
                elif "ILIKE" in c:
                    ok &= any(x.lower() in str(r.get("place", "")).lower() for x in re.findall(r"'%([^%]+)%'", c))
                else:
                    raise AssertionError(f"unsupported cond {c}")
            if ok:
                rows.append(tuple(r.get(c) for c in cols))
        return FakeResult(cols, rows)


def _sighting(**kw):
    base = {"id": str(uuid4()), "org_id": ORG, "date": "2025-05-01", "place": "F, Ostpark", "species": "Kanadagans", "ring": None, "reading": None, "color_ring_color": None, "color_ring_text_color": None, "color_ring_code": None, "area": None}
    base.update(kw)
    return base


@pytest.fixture
def env(tmp_path, monkeypatch):
    tables = {
        "sightings": [
            _sighting(ring="W408", reading="W408"),
            _sighting(ring="W408", reading="W408", date="2025-06-02"),
            _sighting(ring="W408", reading="W408", color_ring_color="white", color_ring_code="W408", org_id=OTHER),
            _sighting(ring="2845731", place="F, Ostpark"),
            _sighting(ring=None, reading="...23886", place="OF, Hafen"),
        ],
        "ringings": [{"id": str(uuid4()), "org_id": ORG, "ring": "2845731", "date": "2019-06-01", "place": "F, Ostpark", "species": "Kanadagans"}],
        "color_rings": [],
    }
    db = FakeReadDB(tables)
    cat = Catalog(tmp_path / "c.sqlite")
    monkeypatch.setattr(runtime, "database", lambda: db)
    monkeypatch.setattr(runtime, "catalog", lambda: cat)
    monkeypatch.setattr(runtime, "definitions", lambda: DefinitionStore(tmp_path / "d.json"))
    monkeypatch.setattr(writes, "settings", types.SimpleNamespace(write_org_id=ORG, write_max_rows=2000, write_proposal_ttl_min=240, write_database_url="postgresql://x", public_base_url="https://x.test", statement_timeout_ms=1000))
    return db, cat, tables


def test_plan_convert_to_color_ring(env):
    db, cat, tables = env
    cs = asyncio.run(plan([ConvertToColorRing(op="convert_to_color_ring", value="W408", ring_color="weiß")], "W408 ist ein Farbring", by="tester"))
    assert cs["status"] == "proposed" and cs["changeset_id"].startswith("chg_")
    items = cat.get("changeset", cs["changeset_id"]).doc["items"]
    sightings = [i for i in items if i["table"] == "sightings"]
    assert len(sightings) == 2 and all(i["org_id"] == ORG for i in sightings)
    assert sightings[0]["after"] == {"color_ring_color": "white", "color_ring_code": "W408", "ring": None}
    assert sightings[0]["before"]["ring"] == "W408"
    reg = [i for i in items if i["table"] == "color_rings"]
    assert len(reg) == 1 and reg[0]["action"] == "insert" and reg[0]["after"]["org_id"] == ORG and reg[0]["after"]["ring"] is None
    assert cs["summary"]["outside_org"] == 1 and any("anderen Organisation" in w for w in cs["warnings"])
    assert any("Organisation:" in line for line in cs["summary"]["lines"])
    assert "Ringfarbe" in cs["plain_summary"] and cs["preview_url"].endswith(cs["changeset_id"])


def test_plan_keeps_metal_ring_when_ringed(env):
    db, cat, tables = env
    tables["sightings"].append(_sighting(ring="2845731", reading="2845731", date="2025-07-01"))
    cs = asyncio.run(plan([ConvertToColorRing(op="convert_to_color_ring", value="2845731", ring_color="red", code="H3")], "Test Metallring", by="t"))
    items = cat.get("changeset", cs["changeset_id"]).doc["items"]
    s = [i for i in items if i["table"] == "sightings"]
    assert all("ring" not in i["after"] for i in s) and any("Metallring" in w for w in cs["warnings"])
    reg = [i for i in items if i["table"] == "color_rings"][0]
    assert reg["after"]["ring"] == "2845731" and reg["after"]["code"] == "H3"


def test_plan_set_fields_skips_and_validates(env):
    db, cat, tables = env
    cs = asyncio.run(plan([SetFields(op="set_fields", target={"ring": "2845731"}, set={"species": "Kanadagans", "status": "BV"})], "Status nachtragen", by="t"))
    doc = cat.get("changeset", cs["changeset_id"]).doc
    assert doc["row_count"] == 1 and doc["items"][0]["after"] == {"status": "BV"} and doc["per_op"][0]["skipped"] == 0
    with pytest.raises(WriteError):
        asyncio.run(plan([SetFields(op="set_fields", target={"ring": "2845731"}, set={"org_id": "x"})], "böse", by="t"))
    with pytest.raises(WriteError):
        asyncio.run(plan([SetFields(op="set_fields", target={"ring": "2845731"}, set={"age": "alt"})], "falscher Typ", by="t"))
    with pytest.raises(ValueError):
        SetFields(op="set_fields", target={}, set={"status": "BV"})


def test_plan_rename_merge_and_limits(env, monkeypatch):
    db, cat, tables = env
    cs = asyncio.run(plan([RenamePlace(op="rename_place", **{"from": "F, Ostpark", "to": "Frankfurt, Ostpark"}), MergeReadingToRing(op="merge_reading_to_ring", reading="...23886", ring="2845731")], "Schreibweise vereinheitlichen", by="t"))
    doc = cat.get("changeset", cs["changeset_id"]).doc
    assert {i["table"] for i in doc["items"]} == {"sightings", "ringings"}
    assert doc["summary"]["field_changes"]["0"]["place"] == 4  # 3 sightings in org + 1 ringing
    merged = [i for i in doc["items"] if i["op"] == 1]
    assert len(merged) == 1 and merged[0]["after"] == {"ring": "2845731"}
    writes.settings.write_max_rows = 2
    with pytest.raises(WriteError):
        asyncio.run(plan([RenamePlace(op="rename_place", **{"from": "F, Ostpark", "to": "X"})], "zu viele", by="t"))
    writes.settings.write_org_id = ""
    with pytest.raises(WriteError):
        asyncio.run(plan([RenamePlace(op="rename_place", **{"from": "F, Ostpark", "to": "X"})], "keine Org", by="t"))


# ---------------------------------------------------------------- apply / rollback with a fake write pool


class FakeCursor:
    def __init__(self, row=None, rowcount=1):
        self._row, self.rowcount = row, rowcount

    async def fetchone(self):
        return self._row


class FakeConn:
    def __init__(self, tables):
        self.tables = tables
        self.log = []

    def transaction(self):
        conn = self

        class Tx:
            async def __aenter__(self):
                conn.snapshot = {t: [dict(r) for r in rows] for t, rows in conn.tables.items()}

            async def __aexit__(self, et, ev, tb):
                if et is not None:  # rollback
                    conn.tables.clear()
                    conn.tables.update(conn.snapshot)
                return False

        return Tx()

    async def execute(self, sql, params=()):
        self.log.append(sql)
        if sql.startswith("SET LOCAL"):
            return FakeCursor()
        m = re.match(r"SELECT (.+?) FROM (\w+) WHERE id = %s AND org_id = %s::uuid FOR UPDATE", sql)
        if m:
            cols = [c.strip() for c in m.group(1).split(",")]
            row = next((r for r in self.tables[m.group(2)] if r["id"] == params[0] and str(r["org_id"]) == params[1]), None)
            return FakeCursor(tuple(row[c] for c in cols) if row else None)
        m = re.match(r"UPDATE (\w+) SET (.+) WHERE id = %s AND org_id = %s::uuid", sql)
        if m:
            cols = [c.split(" = ")[0].strip() for c in m.group(2).split(", ") if "CURRENT_TIMESTAMP" not in c]
            row = next((r for r in self.tables[m.group(1)] if r["id"] == params[-2]), None)
            for c, v in zip(cols, params):
                row[c] = v
            return FakeCursor(rowcount=1 if row else 0)
        m = re.match(r"INSERT INTO (\w+) \((.+)\) VALUES \(.+\) RETURNING id", sql)
        if m:
            cols = [c.strip() for c in m.group(2).split(",")]
            new = dict(zip(cols, params))
            new["id"] = str(uuid4())
            self.tables[m.group(1)].append(new)
            return FakeCursor((new["id"],))
        raise AssertionError(sql)


class FakePool:
    def __init__(self, tables):
        self.conn = FakeConn(tables)

    async def open(self):
        pass

    def connection(self):
        pool = self

        class Ctx:
            async def __aenter__(self):
                return pool.conn

            async def __aexit__(self, *a):
                return False

        return Ctx()


def test_apply_and_rollback_happy_path(env):
    db, cat, tables = env
    cs = asyncio.run(plan([ConvertToColorRing(op="convert_to_color_ring", value="W408", ring_color="white")], "W408 ist ein Farbring", by="t"))
    pool = FakePool(tables)
    out = asyncio.run(writes.apply(cs["changeset_id"], by="ingo", pool=pool))
    assert out["status"] == "applied" and out["applied_at"]
    changed = [r for r in tables["sightings"] if r["reading"] == "W408" and str(r["org_id"]) == ORG]
    assert all(r["ring"] is None and r["color_ring_color"] == "white" and r["color_ring_code"] == "W408" for r in changed)
    untouched = [r for r in tables["sightings"] if str(r["org_id"]) == OTHER][0]
    assert untouched["ring"] == "W408"
    assert len(tables["color_rings"]) == 1 and tables["color_rings"][0]["org_id"] == ORG
    with pytest.raises(WriteError):  # cannot apply twice
        asyncio.run(writes.apply(cs["changeset_id"], by="ingo", pool=pool))
    back = asyncio.run(writes.rollback(cs["changeset_id"], by="ingo", pool=pool))
    assert back["status"] == "rolled_back" and len(back["manual_steps"]) == 1
    assert all(r["ring"] == "W408" and r["color_ring_color"] is None for r in changed)


def test_apply_aborts_when_row_changed_meanwhile(env):
    db, cat, tables = env
    cs = asyncio.run(plan([SetFields(op="set_fields", target={"ring": "2845731"}, set={"status": "BV"})], "Status setzen", by="t"))
    row = next(r for r in tables["sightings"] if r["ring"] == "2845731")
    row["status"] = "MG"  # someone edited in the app meanwhile
    pool = FakePool(tables)
    with pytest.raises(WriteError) as exc:
        asyncio.run(writes.apply(cs["changeset_id"], by="ingo", pool=pool))
    assert "zwischenzeitlich" in str(exc.value)
    doc = cat.get("changeset", cs["changeset_id"]).doc
    assert doc["status"] == "proposed" and "zwischenzeitlich" in doc["last_error"]
    assert row["status"] == "MG"


def test_apply_requires_write_url(env, monkeypatch):
    db, cat, tables = env
    cs = asyncio.run(plan([SetFields(op="set_fields", target={"ring": "2845731"}, set={"status": "BV"})], "Status setzen", by="t"))
    writes.settings.write_database_url = ""
    monkeypatch.setattr(writes, "_write_pool", None)
    with pytest.raises(WriteError) as exc:
        asyncio.run(writes.apply(cs["changeset_id"], by="ingo"))
    assert "nicht freigeschaltet" in str(exc.value)
    assert writes.list_changes(status="proposed")[0]["changeset_id"] == cs["changeset_id"]
    assert writes.get(cs["changeset_id"])["examples"]


def test_changes_page_renders(env):
    from jinja2 import Environment, FileSystemLoader
    from pathlib import Path
    from vogelring_analytics import api_writes

    db, cat, tables = env
    cs = asyncio.run(plan([ConvertToColorRing(op="convert_to_color_ring", value="W408", ring_color="white")], "W408 ist ein Farbring", by="t"))
    jenv = Environment(loader=FileSystemLoader(str(Path(api_writes.__file__).parent / "render" / "templates")), autoescape=True)
    html = api_writes.render_changes_page(jenv, cs["changeset_id"])
    assert "Vorschlag – noch nicht übernommen" in html and "Farbringcode" in html and "W408" in html and "vogelring.com/entries/" in html
