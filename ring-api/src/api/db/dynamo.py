import boto3
from boto3.dynamodb.conditions import Key
from api.models.ringing import Ringing
from api.models.family import FamilyTreeEntry
from decimal import Decimal

client = None
FT_SUFFIX = "#FT"


def get_dynamodb_client():
    global client
    if client is None:
        client = boto3.resource("dynamodb")
    return client


def convert_dynamo_item(item: dict) -> Ringing | FamilyTreeEntry:
    if item.get("ring") is not None and item.get("ring").endswith(FT_SUFFIX):
        item["ring"] = item["ring"][: -len(FT_SUFFIX)]
        return FamilyTreeEntry(**item)
    return Ringing(**item)


# Ringing
def convert_ringing_to_dynamo_item(ringing: Ringing) -> dict:
    """Convert a Ringing object to a DynamoDB item format."""
    item = ringing.model_dump()
    # Convert float values to Decimal for DynamoDB
    item["lat"] = Decimal(str(item["lat"]))
    item["lon"] = Decimal(str(item["lon"]))
    return item


def put_ringing(ringing: Ringing) -> None:
    """Put a Ringing item into DynamoDB."""
    table = get_dynamodb_client().Table("vogelring")
    item = convert_ringing_to_dynamo_item(ringing)
    table.put_item(Item=item)


def delete_ringing(ring: str) -> None:
    """Delete a Ringing item from DynamoDB using its ring number."""
    table = get_dynamodb_client().Table("vogelring")
    table.delete_item(Key={"ring": ring})


def get_ringing_by_ring(ring: str) -> Ringing | None:
    table = get_dynamodb_client().Table("vogelring")

    response = table.query(KeyConditionExpression=Key("ring").eq(ring))

    if len(response["Items"]) == 0:
        return None
    return convert_dynamo_item(response["Items"][0])


# Family Tree Entry


def convert_family_tree_entry_to_dynamo_item(family_tree_entry: FamilyTreeEntry) -> dict:
    item = family_tree_entry.model_dump()
    item["ring"] = item["ring"] + FT_SUFFIX
    return item


def get_family_tree_entry_by_ring(ring: str) -> FamilyTreeEntry | None:
    table = get_dynamodb_client().Table("vogelring")
    response = table.query(KeyConditionExpression=Key("ring").eq(ring + FT_SUFFIX))
    if len(response["Items"]) == 0:
        return None
    return convert_dynamo_item(response["Items"][0])


def delete_family_tree_entry(ring: str) -> None:
    table = get_dynamodb_client().Table("vogelring")
    table.delete_item(Key={"ring": ring + FT_SUFFIX})


def put_family_tree_entry(family_tree_entry: FamilyTreeEntry) -> None:
    table = get_dynamodb_client().Table("vogelring")
    item = convert_family_tree_entry_to_dynamo_item(family_tree_entry)
    table.put_item(Item=item)


if __name__ == "__main__":
    print(delete_family_tree_entry("anton2"))
