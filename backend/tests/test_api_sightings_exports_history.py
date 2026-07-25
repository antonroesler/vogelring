"""
Tests for export-run history and the bulk "gemeldet" update.

The export itself never touches the melded flag — the Vogelwarte confirms a
delivery days later. These endpoints record what went out and flip the flag for
exactly that set once it is accepted.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from src.database.models import Sighting, SightingExport, SightingExportItem
from src.database.user_models import User


EXPORT_URL = "/api/sightings/export/vogelwarte"
RUNS_URL = "/api/sightings/exports"
BACKFILL_URL = "/api/sightings/exports/backfill"


@pytest.fixture
def dev_org_id(client, test_db):
    """Warm up the dev user (created on first authed request) and return its org_id."""
    client.get("/api/sightings/count")
    user = test_db.query(User).filter(User.email == "dev@vogelring.local").first()
    return user.org_id


def _add(test_db, org_id, **kwargs):
    sighting = Sighting(id=uuid4(), org_id=org_id, **kwargs)
    test_db.add(sighting)
    test_db.commit()
    return sighting


class TestExportRunRecording:
    def test_export_records_a_run_with_its_sightings(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1), place="Ort A")
        _add(test_db, dev_org_id, ring="A2", date=date(2026, 3, 2), place="Ort B")

        assert client.get(EXPORT_URL).status_code == 200

        runs = client.get(RUNS_URL).json()
        assert len(runs) == 1
        assert runs[0]["row_count"] == 2
        assert runs[0]["source"] == "export"
        assert runs[0]["pending_count"] == 2
        assert runs[0]["marked_melded_at"] is None
        assert runs[0]["filename"].endswith(".xlsx")

    def test_export_does_not_change_melded(self, client, test_db, dev_org_id):
        sighting = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))

        client.get(EXPORT_URL)

        test_db.refresh(sighting)
        assert sighting.melded is not True

    def test_empty_export_records_no_run(self, client, dev_org_id):
        assert client.get(EXPORT_URL).status_code == 200
        assert client.get(RUNS_URL).json() == []

    def test_run_stores_the_requested_date_range(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))

        client.get(EXPORT_URL, params={"start_date": "2026-02-01", "end_date": "2026-04-01"})

        run = client.get(RUNS_URL).json()[0]
        assert run["start_date"] == "2026-02-01"
        assert run["end_date"] == "2026-04-01"

    def test_run_contains_only_the_exported_sightings(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="IN", date=date(2026, 3, 1))
        # Outside the exported range — must not end up in the run.
        _add(test_db, dev_org_id, ring="OUT", date=date(2026, 8, 1))

        client.get(EXPORT_URL, params={"start_date": "2026-01-01", "end_date": "2026-06-30"})

        run_id = client.get(RUNS_URL).json()[0]["id"]
        items = client.get(f"{RUNS_URL}/{run_id}/sightings").json()
        assert [i["ring"] for i in items] == ["IN"]

    def test_already_melded_sightings_are_not_exported(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="NEW", date=date(2026, 3, 1))
        _add(test_db, dev_org_id, ring="OLD", date=date(2026, 3, 2), melded=True)

        client.get(EXPORT_URL)

        run_id = client.get(RUNS_URL).json()[0]["id"]
        items = client.get(f"{RUNS_URL}/{run_id}/sightings").json()
        assert [i["ring"] for i in items] == ["NEW"]

    def test_runs_are_scoped_to_the_org(self, client, test_db, dev_org_id):
        other_org = uuid4()
        test_db.add(
            SightingExport(
                id=uuid4(), org_id=other_org, row_count=3, source="export"
            )
        )
        test_db.commit()

        assert client.get(RUNS_URL).json() == []

    def test_runs_are_newest_first(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        client.get(EXPORT_URL, params={"start_date": "2026-01-01"})
        _add(test_db, dev_org_id, ring="A2", date=date(2026, 3, 2))
        client.get(EXPORT_URL, params={"start_date": "2026-02-01"})

        runs = client.get(RUNS_URL).json()
        assert [r["start_date"] for r in runs] == ["2026-02-01", "2026-01-01"]


class TestMarkMelded:
    def _export_run_id(self, client):
        client.get(EXPORT_URL)
        return client.get(RUNS_URL).json()[0]["id"]

    def test_marks_every_sighting_of_the_run(self, client, test_db, dev_org_id):
        a = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        b = _add(test_db, dev_org_id, ring="A2", date=date(2026, 3, 2))
        run_id = self._export_run_id(client)

        result = client.post(f"{RUNS_URL}/{run_id}/mark-melded").json()

        assert result["marked"] == 2
        assert result["total"] == 2
        test_db.expire_all()
        assert test_db.get(Sighting, a.id).melded is True
        assert test_db.get(Sighting, b.id).melded is True

    def test_does_not_touch_sightings_outside_the_run(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="IN", date=date(2026, 3, 1))
        run_id = self._export_run_id(client)
        # Entered after the export was taken.
        later = _add(test_db, dev_org_id, ring="LATER", date=date(2026, 3, 5))

        client.post(f"{RUNS_URL}/{run_id}/mark-melded")

        test_db.expire_all()
        assert test_db.get(Sighting, later.id).melded is not True

    def test_run_reports_zero_pending_after_marking(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        run_id = self._export_run_id(client)

        client.post(f"{RUNS_URL}/{run_id}/mark-melded")

        run = client.get(RUNS_URL).json()[0]
        assert run["pending_count"] == 0
        assert run["marked_count"] == 1
        assert run["marked_melded_at"] is not None

    def test_marking_twice_is_idempotent(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        run_id = self._export_run_id(client)

        first = client.post(f"{RUNS_URL}/{run_id}/mark-melded").json()
        second = client.post(f"{RUNS_URL}/{run_id}/mark-melded").json()

        assert first["marked"] == 1
        assert second["marked"] == 0
        assert second["already_melded"] == 1
        assert client.get(RUNS_URL).json()[0]["marked_count"] == 1

    def test_unknown_run_is_404(self, client, dev_org_id):
        assert client.post(f"{RUNS_URL}/{uuid4()}/mark-melded").status_code == 404
        assert client.post(f"{RUNS_URL}/not-a-uuid/mark-melded").status_code == 404

    def test_cannot_mark_another_orgs_run(self, client, test_db, dev_org_id):
        foreign = SightingExport(id=uuid4(), org_id=uuid4(), row_count=0, source="export")
        test_db.add(foreign)
        test_db.commit()

        assert client.post(f"{RUNS_URL}/{foreign.id}/mark-melded").status_code == 404


class TestUnmarkMelded:
    def test_undo_restores_only_what_the_run_flipped(self, client, test_db, dev_org_id):
        flipped = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        client.get(EXPORT_URL)
        run_id = client.get(RUNS_URL).json()[0]["id"]
        client.post(f"{RUNS_URL}/{run_id}/mark-melded")

        # Already gemeldet before this run — it is not part of the run at all.
        untouched = _add(test_db, dev_org_id, ring="A2", date=date(2026, 3, 2), melded=True)

        result = client.post(f"{RUNS_URL}/{run_id}/unmark-melded").json()

        assert result["unmarked"] == 1
        test_db.expire_all()
        assert test_db.get(Sighting, flipped.id).melded is False
        assert test_db.get(Sighting, untouched.id).melded is True

    def test_undo_clears_the_marked_state(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        client.get(EXPORT_URL)
        run_id = client.get(RUNS_URL).json()[0]["id"]
        client.post(f"{RUNS_URL}/{run_id}/mark-melded")

        client.post(f"{RUNS_URL}/{run_id}/unmark-melded")

        run = client.get(RUNS_URL).json()[0]
        assert run["marked_melded_at"] is None
        assert run["pending_count"] == 1

    def test_undo_then_remark_works(self, client, test_db, dev_org_id):
        sighting = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        client.get(EXPORT_URL)
        run_id = client.get(RUNS_URL).json()[0]["id"]

        client.post(f"{RUNS_URL}/{run_id}/mark-melded")
        client.post(f"{RUNS_URL}/{run_id}/unmark-melded")
        result = client.post(f"{RUNS_URL}/{run_id}/mark-melded").json()

        assert result["marked"] == 1
        test_db.expire_all()
        assert test_db.get(Sighting, sighting.id).melded is True


class TestBackfill:
    """Ingo's export already went out before runs were recorded — reconstruct it."""

    def test_dry_run_reports_matches_without_writing(self, client, test_db, dev_org_id):
        sighting = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))

        result = client.post(
            BACKFILL_URL,
            json={"start_date": "2026-01-01", "end_date": "2026-06-30"},
        ).json()

        assert result["dry_run"] is True
        assert result["matched"] == 1
        assert result["run"] is None
        test_db.refresh(sighting)
        assert sighting.melded is not True
        assert client.get(RUNS_URL).json() == []

    def test_dry_run_is_the_default(self, client, test_db, dev_org_id):
        sighting = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))

        client.post(BACKFILL_URL, json={"start_date": "2026-01-01"})

        test_db.refresh(sighting)
        assert sighting.melded is not True

    def test_commit_marks_the_range_and_records_a_run(self, client, test_db, dev_org_id):
        inside = _add(test_db, dev_org_id, ring="IN", date=date(2026, 3, 1))
        outside = _add(test_db, dev_org_id, ring="OUT", date=date(2026, 8, 1))

        result = client.post(
            BACKFILL_URL,
            json={
                "start_date": "2026-01-01",
                "end_date": "2026-06-30",
                "dry_run": False,
                "note": "Export Ingo KW29",
            },
        ).json()

        assert result["marked"] == 1
        test_db.expire_all()
        assert test_db.get(Sighting, inside.id).melded is True
        assert test_db.get(Sighting, outside.id).melded is not True

        run = client.get(RUNS_URL).json()[0]
        assert run["source"] == "manual"
        assert run["note"] == "Export Ingo KW29"
        assert run["pending_count"] == 0
        assert run["marked_count"] == 1

    def test_respects_the_end_date_boundaries_inclusively(self, client, test_db, dev_org_id):
        first = _add(test_db, dev_org_id, ring="FIRST", date=date(2026, 1, 1))
        last = _add(test_db, dev_org_id, ring="LAST", date=date(2026, 6, 30))
        before = _add(test_db, dev_org_id, ring="BEFORE", date=date(2025, 12, 31))

        client.post(
            BACKFILL_URL,
            json={
                "start_date": "2026-01-01",
                "end_date": "2026-06-30",
                "dry_run": False,
            },
        )

        test_db.expire_all()
        assert test_db.get(Sighting, first.id).melded is True
        assert test_db.get(Sighting, last.id).melded is True
        assert test_db.get(Sighting, before.id).melded is not True

    def test_created_before_excludes_later_entries(self, client, test_db, dev_org_id):
        """Entries added after the export was taken must not be swept in."""
        old = _add(test_db, dev_org_id, ring="OLD", date=date(2026, 3, 1))
        new = _add(test_db, dev_org_id, ring="NEW", date=date(2026, 3, 2))
        # Backdate one row's creation to sit before the cut-off.
        cutoff = new.created_at
        old.created_at = cutoff - timedelta(days=1)
        test_db.commit()

        result = client.post(
            BACKFILL_URL,
            json={
                "start_date": "2026-01-01",
                "created_before": (cutoff - timedelta(seconds=1)).isoformat(),
                "dry_run": False,
            },
        ).json()

        assert result["marked"] == 1
        test_db.expire_all()
        assert test_db.get(Sighting, old.id).melded is True
        assert test_db.get(Sighting, new.id).melded is not True

    def test_commit_with_no_matches_is_rejected(self, client, dev_org_id):
        response = client.post(
            BACKFILL_URL, json={"start_date": "2026-01-01", "dry_run": False}
        )
        assert response.status_code == 400

    def test_backfilled_run_can_be_undone(self, client, test_db, dev_org_id):
        sighting = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        run = client.post(
            BACKFILL_URL, json={"start_date": "2026-01-01", "dry_run": False}
        ).json()["run"]

        client.post(f"{RUNS_URL}/{run['id']}/unmark-melded")

        test_db.expire_all()
        assert test_db.get(Sighting, sighting.id).melded is False

    def test_backfill_skips_already_melded_sightings(self, client, test_db, dev_org_id):
        already = _add(test_db, dev_org_id, ring="OLD", date=date(2026, 3, 1), melded=True)
        pending = _add(test_db, dev_org_id, ring="NEW", date=date(2026, 3, 2))

        result = client.post(
            BACKFILL_URL, json={"start_date": "2026-01-01", "dry_run": False}
        ).json()

        assert result["marked"] == 1
        run_id = result["run"]["id"]
        items = client.get(f"{RUNS_URL}/{run_id}/sightings").json()
        assert [i["ring"] for i in items] == ["NEW"]
        # Undo must not un-report the one that was already gemeldet.
        client.post(f"{RUNS_URL}/{run_id}/unmark-melded")
        test_db.expire_all()
        assert test_db.get(Sighting, already.id).melded is True
        assert test_db.get(Sighting, pending.id).melded is False


class TestExportItemsView:
    def test_items_show_current_melded_state(self, client, test_db, dev_org_id):
        _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1), place="Ort A")
        client.get(EXPORT_URL)
        run_id = client.get(RUNS_URL).json()[0]["id"]

        before = client.get(f"{RUNS_URL}/{run_id}/sightings").json()
        assert before[0]["melded"] is False

        client.post(f"{RUNS_URL}/{run_id}/mark-melded")

        after = client.get(f"{RUNS_URL}/{run_id}/sightings").json()
        assert after[0]["melded"] is True
        assert after[0]["place"] == "Ort A"

    def test_items_of_unknown_run_are_404(self, client, dev_org_id):
        assert client.get(f"{RUNS_URL}/{uuid4()}/sightings").status_code == 404

    def test_deleting_a_sighting_keeps_the_run_record(self, client, test_db, dev_org_id):
        sighting = _add(test_db, dev_org_id, ring="A1", date=date(2026, 3, 1))
        client.get(EXPORT_URL)
        run_id = client.get(RUNS_URL).json()[0]["id"]

        test_db.delete(sighting)
        test_db.commit()

        run = client.get(RUNS_URL).json()[0]
        assert run["row_count"] == 1
        assert run["pending_count"] == 0
        assert (
            test_db.query(SightingExportItem)
            .filter(SightingExportItem.export_id == run_id)
            .count()
            == 1
        )
