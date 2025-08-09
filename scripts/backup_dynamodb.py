import boto3
import json
import tqdm
from decimal import Decimal


SOURCE_TABLE = "vogelring"
SINK_LOCATION = "/Users/anton/Projects/vogelring/data/backups/ringing/2025-07-26/"


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to int if it's a whole number, otherwise to float
            if obj % 1 == 0:
                return int(obj)
            else:
                return float(obj)
        return super(DecimalEncoder, self).default(obj)


def backup_dynamodb():
    dynamodb = boto3.resource("dynamodb")
    source_table = dynamodb.Table(SOURCE_TABLE)

    response = source_table.scan()
    for item in tqdm.tqdm(response["Items"], desc="Backing up DynamoDB"):
        with open(f"{SINK_LOCATION}/{item['ring']}.json", "w") as f:
            json.dump(item, f, cls=DecimalEncoder, indent=2)


if __name__ == "__main__":
    backup_dynamodb()
