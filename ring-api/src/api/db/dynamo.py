import boto3
from boto3.dynamodb.conditions import Key
from api.models.ringing import Ringing

client = None


def get_dynamodb_client():
    global client
    if client is None:
        client = boto3.resource("dynamodb")
    return client


def convert_dynamo_item(item: dict) -> Ringing:
    return Ringing(**item)


def get_ringing_by_ring(ring: str) -> Ringing | None:
    table = get_dynamodb_client().Table("vogelring")

    response = table.query(KeyConditionExpression=Key("ring").eq(ring))

    if len(response["Items"]) == 0:
        return None
    print(response["Items"])
    print(response["Items"][0])
    return convert_dynamo_item(response["Items"][0])


if __name__ == "__main__":
    print(get_ringing_by_ring("280705"))
