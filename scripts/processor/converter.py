from pathlib import Path
from enum import Enum
import pickle
from datetime import datetime
from api.models.sightings import Sighting, BirdStatus, BirdAge, PairType
import csv
import random
import math


outfile = Path("data/pkl/sightings-jan-5.pkl")
infile = Path("/Users/anton/Documents/export-jan-5/main.csv")
orte_file = Path("/Users/anton/Documents/export-jan-5/places.csv")


class SightingCols(Enum):
    species = 0
    ring = 2
    reading = 4
    date = 7
    place = 8
    area = 11
    age = 13
    breed_size = 14
    family_size = 15
    pair = 16
    small_group_size = 17
    large_group_size = 18
    partner = 19
    status = 20
    habitat = 21
    field_fruit = 22
    comment = 23
    melder = 24
    melded = 25


def remove_all_non_letter_chars(s: str) -> str:
    return "".join(e for e in s if e.isalpha())


with open(infile) as f:
    data = list(csv.reader(f, delimiter=";"))

with open(orte_file) as f:
    place_data = list(csv.reader(f, delimiter=";"))

# Turn "50,234" formated numbers into float (50.234) values
for p in place_data[1:]:
    if p[1] != "":
        p[1] = float(p[1].replace(" ", "").replace(",", "."))
    if p[2] != "":
        p[2] = float(p[2].replace(" ", "").replace(",", "."))


places = {remove_all_non_letter_chars(p[0]): p for p in place_data}


s = []


def parse_status(status: str) -> BirdStatus | None:
    match status:
        case "BV":
            return BirdStatus.BV
        case "MG":
            return BirdStatus.MG
        case "NB":
            return BirdStatus.NB
        case _:
            return None


def parse_age(age: str) -> BirdAge | None:
    age = age.lower().replace(" ", "").replace(".", "")

    match age:
        case "ad":
            return BirdAge.AD
        case "dj":
            return BirdAge.DJ
        case "juv":
            return BirdAge.JUV
        case "vj":
            return BirdAge.VJ
        case _:
            return None


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


def remove_all_non_numeric(s: str) -> str:
    return "".join(e for e in s if e.isdigit())


def extract_group_size(group_size_str: str) -> int | None:
    if group_size_str == "":
        return None
    try:
        return int(group_size_str)
    except:
        try:
            return int(remove_all_non_numeric(group_size_str))
        except:
            return None


def fmt_str(s: str) -> str:
    return s.replace('"', "").replace("'", "")


def capitalize_first_letter(s: str) -> str:
    return s[0].upper() + s[1:]


def extract_field_fruit(field_fruit: str) -> str:
    f = remove_all_non_letter_chars(field_fruit)
    return capitalize_first_letter(f) if f else None


def extract_sighting_data(entry: list[str]) -> dict:
    # Convert row to json
    json_data = {c.name: entry[c.value] for c in SightingCols if entry[c.value] != "" and c.value != "id"}

    # Date
    json_data["date"] = parse_date(entry[SightingCols.date.value])

    # Group
    json_data["small_group_size"] = extract_group_size(entry[SightingCols.small_group_size.value])
    json_data["large_group_size"] = extract_group_size(entry[SightingCols.large_group_size.value])

    # Clean up comment, melder and place fields by removing quotes
    if "comment" in json_data:
        json_data["comment"] = fmt_str(json_data["comment"])
    if "melder" in json_data:
        json_data["melder"] = fmt_str(json_data["melder"])
    if "place" in json_data:
        json_data["place"] = fmt_str(json_data["place"])

    json_data["melded"] = not (json_data.get("melded", "") == "x")

    json_data["age"] = parse_age(entry[SightingCols.age.value])
    json_data["status"] = parse_status(entry[SightingCols.status.value])
    json_data["habitat"] = None if entry[SightingCols.habitat.value] in ["0", ""] else entry[SightingCols.habitat.value]
    json_data["field_fruit"] = extract_field_fruit(entry[SightingCols.field_fruit.value])
    json_data["breed_size"] = extract_group_size(entry[SightingCols.breed_size.value])
    json_data["family_size"] = extract_group_size(entry[SightingCols.family_size.value])
    json_data["pair"] = (
        entry[SightingCols.pair.value].strip() if entry[SightingCols.pair.value].strip() in ["x", "F", "S"] else None
    )

    return json_data


def add_coordinates(json_data: dict, places: dict) -> dict:
    if "place" in json_data and (p := places.get(remove_all_non_letter_chars(json_data["place"]))):
        # Generate random angle and radius for circular distribution
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, 0.0009)  # Max radius same as previous square diagonal

        # Convert polar coordinates to lat/lon offsets
        json_data["lat"] = float(p[1]) + radius * math.cos(angle) if p[1] else None
        json_data["lon"] = float(p[2]) + radius * math.sin(angle) if p[2] else None
    return json_data


eid = 0
for entry in data[1:]:
    eid += 1
    json_data = extract_sighting_data(entry)
    json_data = add_coordinates(json_data, places)
    # Skip entries without any bird identification data
    if not any(len(json_data.get(field, "")) > 0 for field in ["species", "ring", "reading"]):
        continue
    s.append(Sighting(**json_data, excel_id=eid))

with open(outfile, "wb+") as f:
    pickle.dump(s, f)
