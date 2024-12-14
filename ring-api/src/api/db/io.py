from typing import Callable
import pickle
import boto3

from api import conf
from api.models.sightings import Sighting

from aws_lambda_powertools import Logger

logger = Logger()

s3 = boto3.client("s3")


# Readers
def local_file_reader(file: str) -> tuple[list[Sighting], str]:
    logger.info(f"Loading sightings from {conf.LOCAL_PATH / file}")
    with open(conf.LOCAL_PATH / file, "rb") as f:
        return pickle.load(f), "local"


def s3_reader(file: str) -> tuple[list[Sighting], str]:
    logger.info(f"Loading sightings from {conf.BUCKET}/{file}")
    obj = s3.get_object(Bucket=conf.BUCKET, Key=file)
    return pickle.loads(obj["Body"].read()), obj["VersionId"]


def get_reader() -> Callable[[str], tuple[list[Sighting], str]]:
    if conf.LOCAL:
        assert conf.LOCAL_PATH is not None, "LOCAL_PATH not set"
        return local_file_reader
    assert conf.BUCKET is not None, "BUCKET not set"
    return s3_reader


# Writers
def local_file_writer(file: str, data: list[Sighting]) -> str:
    logger.info(f"Saving sightings to {conf.LOCAL_PATH / file}")
    with open(conf.LOCAL_PATH / file, "wb") as f:
        pickle.dump(data, f)
    return "local"


def s3_writer(file: str, data: list[Sighting]) -> str:
    logger.info(f"Saving sightings to {conf.BUCKET}/{file}")
    res = s3.put_object(Bucket=conf.BUCKET, Key=file, Body=pickle.dumps(data))
    return res["VersionId"]


def get_writer() -> Callable[[str, list[Sighting]], str]:
    if conf.LOCAL:
        assert conf.LOCAL_PATH is not None, "LOCAL_PATH not set"
        return local_file_writer
    assert conf.BUCKET is not None, "BUCKET not set"
    return s3_writer


# Version reader


def local_file_version_reader(file: str) -> str:
    logger.info(f"Loading version from {conf.LOCAL_PATH / file}")
    return "local"


def s3_version_reader(file: str) -> str:
    logger.info(f"Loading version from {conf.BUCKET}/{file}")
    obj = s3.get_object(Bucket=conf.BUCKET, Key=file)
    return obj["VersionId"]


def get_version_reader() -> Callable[[str], str]:
    if conf.LOCAL:
        return local_file_version_reader
    assert conf.BUCKET is not None, "BUCKET not set"
    return s3_version_reader
