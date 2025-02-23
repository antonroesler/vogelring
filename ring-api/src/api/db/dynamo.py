import boto3
from boto3.dynamodb.conditions import Key
from api.models.ringing import Ringing
from decimal import Decimal

client = None


def get_dynamodb_client():
    global client
    if client is None:
        client = boto3.resource("dynamodb")
    return client


def convert_dynamo_item(item: dict) -> Ringing:
    return Ringing(**item)


def convert_to_dynamo_item(ringing: Ringing) -> dict:
    """Convert a Ringing object to a DynamoDB item format."""
    item = ringing.model_dump()
    # Convert float values to Decimal for DynamoDB
    item["lat"] = Decimal(str(item["lat"]))
    item["lon"] = Decimal(str(item["lon"]))
    return item


def put_ringing(ringing: Ringing) -> None:
    """Put a Ringing item into DynamoDB."""
    table = get_dynamodb_client().Table("vogelring")
    item = convert_to_dynamo_item(ringing)
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


if __name__ == "__main__":
    print(get_ringing_by_ring("280705"))
