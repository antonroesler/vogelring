import asyncio

from vogelring_analytics.catalog import Catalog
from vogelring_analytics.events import EventBus


def test_catalog_put_get_list_search(tmp_path):
    cat = Catalog(tmp_path / "c.sqlite")
    a = cat.put("view", {"kind": "chart"}, title="Kanadagänse je Monat", description="Ostpark 2025", owner="ingo@x", tags=["ostpark"])
    b = cat.put("view", {"kind": "map"}, title="Karte", owner="ingo@x")
    assert a.id.startswith("vw_") and cat.get("view", a.id).doc == {"kind": "chart"}
    assert [i.id for i in cat.list("view")] == [b.id, a.id]
    assert [i.id for i in cat.list("view", search="ostpark")] == [a.id]
    cat.set_pinned("view", a.id, True)
    assert cat.list("view")[0].id == a.id and cat.list("view")[0].pinned
    upd = cat.put("view", {"kind": "chart", "x": 1}, id=a.id, title="Neu")
    assert upd.created_at == a.created_at and upd.title == "Neu" and upd.pinned and upd.owner == "ingo@x"
    assert cat.counts() == {"view": 2}
    assert cat.delete("view", b.id) and not cat.exists("view", b.id)


def test_activity_log(tmp_path):
    cat = Catalog(tmp_path / "c.sqlite")
    cat.log_event("2026-01-01T00:00:00+00:00", "visual.created", "Karte erstellt", {"visual_id": "vz_1"})
    cat.log_event("2026-01-01T00:00:01+00:00", "note.created", "Notiz", {})
    items = cat.activity(limit=10, types=["visual.created"])
    assert len(items) == 1 and items[0]["visual_id"] == "vz_1"


def test_event_bus_publish_subscribe():
    async def main():
        bus = EventBus()
        seen = []
        bus.bind(asyncio.get_running_loop(), persist=lambda ev: seen.append(ev.type))
        q = bus.subscribe()
        bus.publish("visual.created", "Karte erstellt", visual_id="vz_1")
        ev = await asyncio.wait_for(q.get(), 1)
        assert ev.type == "visual.created" and ev.payload["visual_id"] == "vz_1" and ev.seq == 1
        assert "event: visual.created" in ev.sse() and seen == ["visual.created"]
        bus.publish("log", "zwei")
        assert [e.seq for e in bus.since(1)] == [2]
        bus.unsubscribe(q)

    asyncio.run(main())
