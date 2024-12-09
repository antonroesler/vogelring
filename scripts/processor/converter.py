from pathlib import Path
from enum import Enum
import pickle
from datetime import datetime
from api.models.sightings import Sighting
import csv

outfile = Path("data/pkl/sightings.pkl")


class SightingCols(Enum):
    excel_id = 0
    species = 1
    ring = 2
    reading = 3
    date = 4
    place = 5
    group_size = 6
    comment = 7
    melder = 8


with open("data/out/main.csv") as f:
    data = list(csv.reader(f))

with open("data/out/orte.csv") as f:
    place_data = list(csv.reader(f, delimiter=";"))

places = {p[1]: p for p in place_data}


s = []


def parse_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%m/%d/%y")
    except ValueError:
        try:
            # Handle European format with comma
            date_str = date_str.replace(",", ".")
            day, month, year = date_str.split(".")
            return datetime(int(year), int(month), int(day))
        except (ValueError, IndexError):
            # Return None for unparseable dates
            return None


def extract_sighting_data(entry: list[str]) -> dict:
    json_data = {c.name: entry[c.value] for c in SightingCols if entry[c.value] != "" and c.value != "id"}

    json_data["date"] = parse_date(entry[SightingCols.date.value])
    return json_data


def add_coordinates(json_data: dict, places: dict) -> dict:
    if "place" in json_data and (p := places.get(json_data["place"])):
        json_data["lat"] = float(p[2]) if p[2] else None
        json_data["lon"] = float(p[3]) if p[3] else None
    return json_data


for entry in data[1:]:
    json_data = extract_sighting_data(entry)
    json_data = add_coordinates(json_data, places)
    s.append(Sighting(**json_data))

with open(outfile, "wb+") as f:
    pickle.dump(s, f)
