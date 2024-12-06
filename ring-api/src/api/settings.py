from pydantic_settings import BaseSettings
from pathlib import Path


class Conf(BaseSettings):
    BUCKET: str | None = None
    LOCAL: bool | None = None
    LOCAL_PATH: Path | None = None
    SIGHTINGS_FILE: str = "sightings.pkl"
