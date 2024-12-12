from pydantic import BaseModel


class RollingYearCountPerMonth(BaseModel):
    year: int
    month: int
    count: int


class SimpleBirdMeta(BaseModel):
    species: str
    ring: str
    sighting_count: int


class SimplePlaceMeta(BaseModel):
    place: str
    count: int


class Dashboard(BaseModel):
    total_sightings: int  # total number of sightings
    total_birds: int  # total number of individual birds
    bird_count_today: int  # number of birds seen today
    bird_count_yesterday: int  # number of birds seen yesterday
    bird_count_this_week: int  # number of birds seen this week
    bird_count_last_week: int  # number of birds seen last week
    strike_day_count: int  # number of consecutive days with sightings until today
    rolling_year_count_per_month_per_species: dict[
        str, list[RollingYearCountPerMonth]
    ]  # number of sightings per month for the last 12 month per species
    top_3_birds_this_year: list[SimpleBirdMeta]  # top 3 birds by number of sightings
    top_3_places_this_year: list[SimplePlaceMeta]  # top 3 places by number of sightings
