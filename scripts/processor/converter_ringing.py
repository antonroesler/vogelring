import csv
from enum import Enum
from datetime import datetime
import boto3
from api.models.ringing import Ringing
from decimal import Decimal


class RingingCols(Enum):
    ring = 1  # A
    ring_scheme = 0  # B
    species = 4  # E
    date = 11  # L Format is 2011-10-03 07:30:00
    place = 30
    lat = 29
    lon = 28
    ringer = 17
    sex = 6
    age = 7


def convert_to_dynamo_item(row):
    # Parse date from string
    date_str = row[RingingCols.date.value]
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()

    # Create Ringing object
    ringing = Ringing(
        ring=row[RingingCols.ring.value],
        ring_scheme=row[RingingCols.ring_scheme.value],
        species=row[RingingCols.species.value],
        date=date_obj,
        place=row[RingingCols.place.value],
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
    with open("data/out/ringing.csv") as f:
        data = list(csv.reader(f, delimiter=";"))

    # Skip header row
    for row in data[1:]:
        try:
            item = convert_to_dynamo_item(row)
            table.put_item(Item=item)
        except Exception as e:
            print(f"Error processing row: {row}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
