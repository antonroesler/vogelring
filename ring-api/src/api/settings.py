from pydantic_settings import BaseSettings
from pathlib import Path


class Conf(BaseSettings):
    BUCKET: str | None = None
    LOCAL: bool | None = None
    LOCAL_PATH: Path | None = None
    SIGHTINGS_FILE: str = "sightings.pkl"
    CLOUDFRONT_DOMAIN: str | None = None
    CLOUDFRONT_KEY_PAIR_ID: str | None = None
    CLOUDFRONT_PRIVATE_KEY_PARAM_NAME: str | None = None
    AWS_REGION: str = "eu-central-1"
