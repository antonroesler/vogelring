"""Map-first place suggestions (/places/nearby) and position plausibility (/places/check)."""

from src.api.services.place_service import format_distance_de

# Frankfurt Ostpark (~50.1180, 8.7150) and Niddapark (~50.1450, 8.6400), ~6 km apart.
OSTPARK = (50.1180, 8.7150)
OSTPARK_NORTH = (50.1195, 8.7140)  # ~170 m north of OSTPARK
NIDDAPARK = (50.1450, 8.6400)


def add_sighting(client, place, latlon, area=None, date="2024-05-01", **extra):
    payload = {"species": "Branta canadensis", "place": place, "area": area, "date": date}
    if latlon is not None:
        payload["lat"], payload["lon"] = latlon
    payload.update(extra)
    response = client.post("/api/sightings", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def add_ringing(client, ring, place, latlon, date="2022-06-10"):
    lat, lon = latlon
    response = client.post(
        "/api/ringing",
        json={
            "ring": ring,
            "ring_scheme": "DEH",
            "species": "Branta canadensis",
            "date": date,
            "place": place,
            "lat": lat,
            "lon": lon,
            "ringer": "Tester",
            "sex": 1,
            "age": 4,
        },
    )
    assert response.status_code in (200, 201), response.text


class TestNearbyPlaces:
    def test_empty_database(self, client):
        response = client.get("/api/places/nearby", params={"lat": 50.1, "lon": 8.7})
        assert response.status_code == 200
        assert response.json() == []

    def test_nearest_first_and_grouped_by_place_and_area(self, client):
        add_sighting(client, "F, Ostpark", OSTPARK, date="2023-04-01")
        add_sighting(client, "F, Ostpark", OSTPARK_NORTH, date="2024-04-01")
        add_sighting(client, "F, Ostpark", OSTPARK_NORTH, area="Nordufer", date="2021-01-01")
        add_sighting(client, "F, Niddapark", NIDDAPARK)
        # Sightings without coordinates or without a place never produce suggestions.
        add_sighting(client, "F, Ohne Koordinaten", None)
        add_sighting(client, None, OSTPARK)

        response = client.get(
            "/api/places/nearby", params={"lat": OSTPARK[0], "lon": OSTPARK[1], "radius_km": 10}
        )
        assert response.status_code == 200
        data = response.json()

        assert [(d["place"], d["area"]) for d in data] == [
            ("F, Ostpark", None),
            ("F, Ostpark", "Nordufer"),
            ("F, Niddapark", None),
        ]
        ostpark = data[0]
        assert ostpark["count"] == 2
        assert ostpark["distance_m"] < 1
        assert ostpark["last_date"] == "2024-04-01"
        assert abs(ostpark["center_lat"] - (OSTPARK[0] + OSTPARK_NORTH[0]) / 2) < 1e-6

        nordufer = data[1]
        assert nordufer["count"] == 1
        assert 100 < nordufer["distance_m"] < 250

        niddapark = data[2]
        assert 5000 < niddapark["distance_m"] < 7000

    def test_radius_and_limit(self, client):
        add_sighting(client, "F, Ostpark", OSTPARK)
        add_sighting(client, "F, Ostpark", OSTPARK_NORTH, area="Nordufer")
        add_sighting(client, "F, Niddapark", NIDDAPARK)

        response = client.get("/api/places/nearby", params={"lat": OSTPARK[0], "lon": OSTPARK[1]})
        assert [d["place"] for d in response.json()] == ["F, Ostpark", "F, Ostpark"]  # 5 km default

        response = client.get(
            "/api/places/nearby", params={"lat": OSTPARK[0], "lon": OSTPARK[1], "limit": 1}
        )
        assert len(response.json()) == 1

    def test_includes_ringing_places(self, client):
        add_ringing(client, "RING1", "F, Beringungsplatz", OSTPARK)

        response = client.get("/api/places/nearby", params={"lat": OSTPARK[0], "lon": OSTPARK[1]})
        data = response.json()
        assert len(data) == 1
        assert data[0]["place"] == "F, Beringungsplatz"
        assert data[0]["area"] is None
        assert data[0]["last_date"] == "2022-06-10"

    def test_validation(self, client):
        assert client.get("/api/places/nearby", params={"lat": 50.1}).status_code == 422
        assert client.get("/api/places/nearby", params={"lat": 95, "lon": 8.7}).status_code == 422


class TestCheckPlace:
    def test_unknown_place_never_warns(self, client):
        response = client.get(
            "/api/places/check", params={"place": "F, Neu", "lat": OSTPARK[0], "lon": OSTPARK[1]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["known"] is False
        assert data["warning"] is False
        assert data["count"] == 0
        assert data["message"] is None

    def test_position_inside_known_area(self, client):
        add_sighting(client, "F, Ostpark", OSTPARK)
        add_sighting(client, "F, Ostpark", OSTPARK_NORTH)

        response = client.get(
            "/api/places/check",
            params={"place": "f, ostpark ", "lat": OSTPARK_NORTH[0], "lon": OSTPARK_NORTH[1]},
        )
        data = response.json()
        assert data["known"] is True
        assert data["count"] == 2
        assert data["nearest_m"] < 1
        assert data["typical_radius_m"] == 250  # minimum radius for a tight cluster
        assert data["warning"] is False
        assert data["message"] is None

    def test_position_far_away_warns_with_german_message(self, client):
        add_sighting(client, "F, Ostpark", OSTPARK)
        add_sighting(client, "F, Ostpark", OSTPARK_NORTH)

        response = client.get(
            "/api/places/check",
            params={"place": "F, Ostpark", "lat": NIDDAPARK[0], "lon": NIDDAPARK[1]},
        )
        data = response.json()
        assert data["known"] is True
        assert data["warning"] is True
        assert 5000 < data["nearest_m"] < 7000
        assert data["message"].startswith("Hinweis: ‚F, Ostpark‘ wurde bisher etwa ")
        assert data["message"].endswith(" km von hier eingetragen.")
        assert "," in data["message"].split("etwa ")[1]  # German decimal comma, e.g. 6,0 km

    def test_wide_spread_place_gets_larger_typical_radius(self, client):
        # A place recorded over a ~6 km stretch: its typical radius grows with it,
        # so a point in between is not flagged.
        add_sighting(client, "Main", OSTPARK)
        add_sighting(client, "Main", NIDDAPARK)
        add_ringing(client, "RING2", "Main", OSTPARK_NORTH)

        middle = ((OSTPARK[0] + NIDDAPARK[0]) / 2, (OSTPARK[1] + NIDDAPARK[1]) / 2)
        response = client.get("/api/places/check", params={"place": "Main", "lat": middle[0], "lon": middle[1]})
        data = response.json()
        assert data["known"] is True
        assert data["count"] == 3
        assert data["typical_radius_m"] > 2000
        assert data["warning"] is False

    def test_validation(self, client):
        assert client.get("/api/places/check", params={"lat": 50.1, "lon": 8.7}).status_code == 422
        assert client.get("/api/places/check", params={"place": "x", "lat": 50.1}).status_code == 422


def test_format_distance_de():
    assert format_distance_de(0) == "0 m"
    assert format_distance_de(123) == "120 m"
    assert format_distance_de(999) == "1000 m"
    assert format_distance_de(2340) == "2,3 km"
    assert format_distance_de(12345) == "12 km"
