from pathlib import Path
from enum import Enum
import pickle
from datetime import datetime
from api.models.sightings import Sighting
import csv
import random
import math


outfile = Path("data/pkl/sightings-2.pkl")
infile = Path("data/main-02.csv")
orte_file = Path("data/out/orte.csv")


class SightingCols(Enum):
    species = 0
    ring = 2
    reading = 4
    date = 7
    place = 8
    habitat = 21
    comment = 22
    melder = 23
    melded = 24
    group_size = 17


def remove_all_non_letter_chars(s: str) -> str:
    return "".join(e for e in s if e.isalpha())


with open(infile) as f:
    data = list(csv.reader(f, delimiter=";"))

with open(orte_file) as f:
    place_data = list(csv.reader(f, delimiter=";"))

places = {remove_all_non_letter_chars(p[1]): p for p in place_data}


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


def extract_group_size(group_size_str: str) -> int | None:
    if group_size_str == "":
        return None
    try:
        return int(group_size_str)
    except:
        return None


def extract_sighting_data(entry: list[str]) -> dict:
    json_data = {c.name: entry[c.value] for c in SightingCols if entry[c.value] != "" and c.value != "id"}

    json_data["date"] = parse_date(entry[SightingCols.date.value])
    json_data["group_size"] = extract_group_size(entry[SightingCols.group_size.value])
    # Clean up comment, melder and place fields by removing quotes
    if "comment" in json_data:
        json_data["comment"] = json_data["comment"].replace('"', "").replace("'", "")
    if "melder" in json_data:
        json_data["melder"] = json_data["melder"].replace('"', "").replace("'", "")
    if "place" in json_data:
        json_data["place"] = json_data["place"].replace('"', "").replace("'", "")
    json_data["melded"] = json_data.get("melded", "") == "x"
    return json_data


def add_coordinates(json_data: dict, places: dict) -> dict:
    if "place" in json_data and (p := places.get(remove_all_non_letter_chars(json_data["place"]))):
        # Generate random angle and radius for circular distribution
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, 0.0009)  # Max radius same as previous square diagonal

        # Convert polar coordinates to lat/lon offsets
        json_data["lat"] = float(p[2]) + radius * math.cos(angle) if p[2] else None
        json_data["lon"] = float(p[3]) + radius * math.sin(angle) if p[3] else None
    return json_data


for entry in data[1:]:
    json_data = extract_sighting_data(entry)
    json_data = add_coordinates(json_data, places)
    # Skip entries without any bird identification data
    if not any(len(json_data.get(field, "")) > 0 for field in ["species", "ring", "reading"]):
        continue
    s.append(Sighting(**json_data))

with open(outfile, "wb+") as f:
    pickle.dump(s, f)
