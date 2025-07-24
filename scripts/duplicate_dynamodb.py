import boto3

SOURCE_TABLE = "vogelring"
SINK_TABLE = "vogelring-dev"


def duplicate_dynamodb():
    dynamodb = boto3.resource("dynamodb")
    source_table = dynamodb.Table(SOURCE_TABLE)
    sink_table = dynamodb.Table(SINK_TABLE)

    # Use batch_writer for efficient batch operations
    with sink_table.batch_writer() as batch:
        # Paginate through scan results to handle large tables
        scan_kwargs = {}
        item_count = 0

        while True:
            response = source_table.scan(**scan_kwargs)

            # Process items in current page
            for item in response["Items"]:
                batch.put_item(Item=item)
                item_count += 1

                # Log progress every 1000 items
                if item_count % 1000 == 0:
                    print(f"Processed {item_count} items...")

            # Check if there are more items to process
            if "LastEvaluatedKey" not in response:
                break

            # Set the starting point for the next page
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]

    print(f"Successfully duplicated {item_count} items from {SOURCE_TABLE} to {SINK_TABLE}")


if __name__ == "__main__":
    duplicate_dynamodb()
