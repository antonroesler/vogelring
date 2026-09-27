"""Farbringe (color rings): parsing, registry, sighting resolution and search"""

import pytest

from src.utils.color_rings import matches_pattern, normalize_code, parse_ring_query


class TestParsing:
    def test_plain_code(self):
        q = parse_ring_query("H3E4")
        assert (q.ring_color, q.text_color, q.code_pattern) == (None, None, "H3E4")

    def test_color_names_and_abbreviations(self):
        q = parse_ring_query("rot/weiß h3e4")
        assert (q.ring_color, q.text_color, q.code_pattern) == ("red", "white", "H3E4")
        q = parse_ring_query("Y H58A")
        assert (q.ring_color, q.code_pattern) == ("yellow", "H58A")

    def test_lone_color_word_is_a_code(self):
        q = parse_ring_query("gelb")
        assert q.ring_color is None
        assert q.code_pattern == "GELB"

    def test_wildcards(self):
        assert parse_ring_query("rot H3…").code_pattern == "H3*"
        assert matches_pattern("H3*", "h3e4")
        assert matches_pattern("*E4", "H3E4")
        assert matches_pattern("H*4", "H3E4")
        assert matches_pattern("3E", "H3E4")
        assert not matches_pattern("H3*", "XH3E4")

    def test_normalize_code(self):
        assert normalize_code(" h3 e4 ") == "H3E4"
        assert normalize_code("  ") is None


def create(client, **data):
    return client.post("/api/color-rings", json=data)


def add_sighting(client, **data):
    response = client.post("/api/sightings", json=data)
    assert response.status_code == 200, response.text
    return response.json()


class TestRegistry:
    def test_same_code_different_color_are_different_rings(self, client):
        assert create(client, ring_color="red", code="H3E4").status_code == 200
        assert create(client, ring_color="yellow", code="H3E4").status_code == 200
        assert create(client, ring_color="red", code="h3e4").status_code == 409

    def test_text_color_distinguishes_rings(self, client):
        assert create(client, ring_color="red", text_color="white", code="A1").status_code == 200
        assert create(client, ring_color="red", text_color="black", code="A1").status_code == 200

    def test_one_color_ring_per_metal_ring(self, client):
        assert create(client, ring="GN1", ring_color="red", code="A1").status_code == 200
        response = create(client, ring="GN1", ring_color="red", code="A2")
        assert response.status_code == 409
        assert "GN1" in response.json()["detail"]

    @pytest.mark.parametrize(
        "data",
        [
            {"ring_color": "purpleish", "code": "A1"},
            {"ring_color": "red", "code": "A1", "mark_type": "tail"},
            {"ring_color": "red", "code": "A1", "leg": "middle"},
        ],
    )
    def test_validation(self, client, data):
        assert create(client, **data).status_code == 400

    def test_optional_fields_roundtrip(self, client):
        response = create(
            client,
            ring_color="yellow",
            text_color="black",
            code="h58a",
            mark_type="leg",
            leg="right",
            project="OAGSH Möwen",
        )
        body = response.json()
        assert body["code"] == "H58A"
        assert body["leg"] == "right"
        assert client.get("/api/color-rings").json()[0]["project"] == "OAGSH Möwen"

    def test_linking_backfills_color_only_sightings(self, client):
        sighting = add_sighting(client, color_ring_color="red", color_ring_code="A1")
        assert sighting["ring"] is None
        color_ring = client.get("/api/color-rings").json()[0]
        assert color_ring["ring"] is None

        response = client.put(f"/api/color-rings/{color_ring['id']}", json={"ring": "GN1"})
        assert response.status_code == 200
        bird = client.get("/api/birds/GN1").json()
        assert bird["sighting_count"] == 1
        assert bird["color_ring"]["code"] == "A1"


class TestSightingResolution:
    def test_color_ring_is_optional(self, client):
        sighting = add_sighting(client, ring="GN1")
        assert sighting["color_ring_code"] is None
        assert client.get("/api/color-rings").json() == []

    def test_incomplete_color_ring_is_rejected(self, client):
        response = client.post("/api/sightings", json={"color_ring_code": "A1"})
        assert response.status_code == 400

    def test_new_color_ring_is_registered_with_metal_ring(self, client):
        add_sighting(client, ring="GN1", color_ring_color="red", color_ring_code="a1")
        [color_ring] = client.get("/api/color-rings").json()
        assert (color_ring["ring"], color_ring["code"]) == ("GN1", "A1")

    def test_known_color_ring_fills_metal_ring(self, client):
        create(client, ring="GN1", ring_color="red", code="A1")
        sighting = add_sighting(client, color_ring_color="red", color_ring_code="A1")
        assert sighting["ring"] == "GN1"

    def test_other_color_does_not_resolve(self, client):
        create(client, ring="GN1", ring_color="red", code="A1")
        sighting = add_sighting(client, color_ring_color="yellow", color_ring_code="A1")
        assert sighting["ring"] is None

    def test_color_only_bird_detail(self, client):
        add_sighting(client, species="Lachmöwe", color_ring_color="red", color_ring_code="A1")
        add_sighting(client, species="Lachmöwe", color_ring_color="red", color_ring_code="A1")
        [color_ring] = client.get("/api/color-rings").json()
        bird = client.get(f"/api/birds/color-ring/{color_ring['id']}").json()
        assert bird["ring"] is None
        assert bird["sighting_count"] == 2
        assert bird["species"] == "Lachmöwe"


class TestSearch:
    @pytest.fixture
    def birds(self, client):
        add_sighting(client, ring="GN102522", species="Lachmöwe")
        add_sighting(client, ring="GN55", species="Silbermöwe", color_ring_color="red", color_ring_code="H3E4")
        add_sighting(client, species="Sturmmöwe", color_ring_color="yellow", color_ring_code="H3E4")

    def suggest(self, client, reading):
        response = client.get(f"/api/birds/suggestions/{reading}")
        assert response.status_code == 200
        return response.json()

    def test_code_without_color_finds_both_rings(self, client, birds):
        result = self.suggest(client, "H3E4")
        assert {r["color_ring"]["ring_color"] for r in result} == {"red", "yellow"}
        assert {r["ring"] for r in result} == {"GN55", None}

    def test_color_narrows_result(self, client, birds):
        [bird] = self.suggest(client, "gelb H3E4")
        assert bird["ring"] is None
        assert bird["species"] == "Sturmmöwe"
        assert bird["sighting_count"] == 1

    def test_metal_ring_still_found_with_wildcards(self, client, birds):
        [bird] = self.suggest(client, "gn1*")
        assert bird["ring"] == "GN102522"
        assert bird["color_ring"] is None

    def test_metal_ring_result_carries_color_ring(self, client, birds):
        [bird] = self.suggest(client, "GN55")
        assert bird["color_ring"]["code"] == "H3E4"

    def test_ringing_list_filter_matches_color_ring(self, client, sample_ringing_data):
        ringing = {**sample_ringing_data, "date": "2023-05-15"}
        assert client.post("/api/ringing", json=ringing).status_code == 200
        create(client, ring=ringing["ring"], ring_color="red", code="XY12")
        for term in ("XY12", "rot XY", "TEST001"):
            rings = [r["ring"] for r in client.get("/api/ringings", params={"ring": term}).json()]
            assert rings == ["TEST001"], term
        assert client.get("/api/ringings", params={"ring": "gelb XY12"}).json() == []


def test_migration_adds_columns_and_is_idempotent(tmp_path):
    import importlib.util
    from sqlalchemy import create_engine, inspect, text

    spec = importlib.util.spec_from_file_location(
        "migrate_color_rings", "scripts/migrate_color_rings.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE organizations (id CHAR(36) PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE sightings (id CHAR(36) PRIMARY KEY, ring VARCHAR(50))"))

    module.migrate(engine)
    module.migrate(engine)

    inspector = inspect(engine)
    columns = {c["name"] for c in inspector.get_columns("sightings")}
    assert set(module.SIGHTING_COLUMNS) <= columns
    assert "color_rings" in inspector.get_table_names()
