import csv
from enum import Enum
from datetime import datetime
import boto3
from api.models.ringing import Ringing
from decimal import Decimal
import sys


def read_places():
    places = dict()
    p = "/Users/anton/Desktop/tblGeoTab.csv"
    with open(p) as f:
        print(f.readline())
        for row in f.readlines():
            row = row.split(";")
            places[row[0]] = row[3]
    return places


place_map = read_places()


class RingingCols(Enum):
    ring = 1  # A
    ring_scheme = 0  # B
    species = 2  # E
    date = 9  # L Format is 2011-10-03 07:30:00
    place_id = 12
    lat = 26
    lon = 27
    ringer = 15
    sex = 4
    age = 5


def convert_to_dynamo_item(row):
    # Parse date from string
    date_str = row[RingingCols.date.value]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()

    # Create Ringing object
    ringing = Ringing(
        ring=row[RingingCols.ring.value].replace(".", "").replace(" ", ""),
        ring_scheme=row[RingingCols.ring_scheme.value],
        species=row[RingingCols.species.value],
        date=date_obj,
        place=place_map[row[RingingCols.place_id.value]],
        lat=float(row[RingingCols.lat.value]),
        lon=float(row[RingingCols.lon.value]),
        ringer=row[RingingCols.ringer.value],
        sex=int(row[RingingCols.sex.value]),
        age=int(row[RingingCols.age.value]),
    )

    # Convert to DynamoDB format
    return {
        "ring": ringing.ring,
        "ring_scheme": ringing.ring_scheme,
        "species": ringing.species,
        "date": ringing.date.isoformat(),
        "place": ringing.place,
        "lat": Decimal(str(ringing.lat)),
        "lon": Decimal(str(ringing.lon)),
        "ringer": ringing.ringer,
        "sex": ringing.sex,
        "age": ringing.age,
        "id": ringing.id,
    }


def main():
    # Initialize DynamoDB client
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("vogelring")

    # Read and process CSV
    with open("/Users/anton/Desktop/tblRinging.csv") as f:
        data = list(csv.reader(f, delimiter=";"))

    # Skip header row
    for row in data[1:]:
        try:
            item = convert_to_dynamo_item(row)
            print(item)
            table.put_item(Item=item)
        except Exception as e:
            print(f"Error processing row: {row}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
