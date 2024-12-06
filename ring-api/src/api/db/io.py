from typing import Callable
import pickle
import boto3

from api import conf
from api.models.sightings import Sighting


# Readers
def local_file_reader(file: str) -> list[Sighting]:
    with open(conf.LOCAL_PATH / file, "rb") as f:
        return pickle.load(f)


def s3_reader(file: str) -> list[Sighting]:
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=conf.BUCKET, Key=file)
    return pickle.loads(obj["Body"].read())


def get_reader() -> Callable[[str], list[Sighting]]:
    if conf.LOCAL:
        assert conf.LOCAL_PATH is not None, "LOCAL_PATH not set"
        return local_file_reader
    assert conf.BUCKET is not None, "BUCKET not set"
    return s3_reader


# Writers
def local_file_writer(file: str, data: list[Sighting]) -> None:
    with open(conf.LOCAL_PATH / file, "wb") as f:
        pickle.dump(data, f)


def s3_writer(file: str, data: list[Sighting]) -> None:
    s3 = boto3.client("s3")
    s3.put_object(Bucket=conf.BUCKET, Key=file, Body=pickle.dumps(data))


def get_writer() -> Callable[[str, list[Sighting]], None]:
    if conf.LOCAL:
        assert conf.LOCAL_PATH is not None, "LOCAL_PATH not set"
        return local_file_writer
    assert conf.BUCKET is not None, "BUCKET not set"
    return s3_writer
