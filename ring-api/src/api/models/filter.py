from pydantic import BaseModel
from datetime import date


class BirdFilter(BaseModel):
    species: str | None = None
    ring: str | None = None
    date_: date | None = None
    place: str | None = None
    melder: str | None = None
    melded: bool | None = None

    def active_fields(self):
        return [arg for arg in self.model_fields if getattr(self, arg)]
