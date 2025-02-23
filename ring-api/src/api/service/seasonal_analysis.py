from datetime import datetime, date
from api.models.sightings import BirdMeta, Sighting
from pydantic import BaseModel, Field
from api.db import loader


class SeasonalCount(BaseModel):
    species: str = Field(description="Species name")
    month: int = Field(description="Month of the year", ge=1, le=12)
    absolute_avg: int = Field(description="Median number of sightings for this species in this month", ge=0)
    relative_avg: float = Field(description="Relative median number of sightings for this species in this month", ge=0)
    q1_avg: int = Field(description="First quartile (Q1) of sightings", ge=0)
    q3_avg: int = Field(description="Third quartile (Q3) of sightings", ge=0)
    max_count: int = Field(description="Maximum number of sightings in this month", ge=0)
    recent_count: int = Field(description="Number of sightings in the most recent occurrence of this month", ge=0)


class SeasonalAnalysis(BaseModel):
    counts: dict[str, list[SeasonalCount]] = Field(description="Counts per species and month")


def get_seasonal_analysis() -> SeasonalAnalysis:
    sightings = loader.get_sightings()
    year_species_counts: dict[str, dict[dict[int, int]]] = {}  # species: year: month: count

    # Get current date for recent counts
    current_date = datetime.now().date()
    current_month = current_date.month
    current_year = current_date.year

    # Initialize recent counts dictionary
    recent_counts: dict[str, dict[int, int]] = {}  # species: month: count

    for sighting in sightings:
        # Regular counts
        if sighting.species not in year_species_counts:
            year_species_counts[sighting.species] = {}
        if sighting.date.year not in year_species_counts[sighting.species]:
            year_species_counts[sighting.species][sighting.date.year] = {k: 0 for k in range(1, 13)}
        year_species_counts[sighting.species][sighting.date.year][sighting.date.month] += 1

        # Recent counts (last 12 months)
        if sighting.species not in recent_counts:
            recent_counts[sighting.species] = {k: 0 for k in range(1, 13)}

        # Check if this sighting is from the last 12 months
        months_diff = (current_year - sighting.date.year) * 12 + (current_month - sighting.date.month)

        if 0 <= months_diff < 12:
            recent_counts[sighting.species][sighting.date.month] += 1

    return SeasonalAnalysis(
        counts={
            species: get_seasonal_counts(species, year_counts, recent_counts.get(species, {}))
            for species, year_counts in year_species_counts.items()
        }
    )


def get_seasonal_counts(
    species: str, counts: dict[str, dict[dict[int, int]]], recent_counts: dict[int, int]
) -> list[SeasonalCount]:
    # Initialize lists to store counts for each month
    month_counts = {month: [] for month in range(1, 13)}

    # Collect all counts for each month across years
    for year_data in counts.values():
        for month, count in year_data.items():
            month_counts[month].append(count)

    # Calculate median and quartiles for each month
    medians = []
    q1s = []
    q3s = []
    maxes = []

    for month in range(1, 13):
        counts_list = month_counts[month]
        if not counts_list:
            medians.append(0)
            q1s.append(0)
            q3s.append(0)
            maxes.append(0)
        else:
            sorted_counts = sorted(counts_list)
            n = len(sorted_counts)

            # Calculate median (Q2)
            if n % 2 == 0:
                median = (sorted_counts[n // 2 - 1] + sorted_counts[n // 2]) / 2
            else:
                median = sorted_counts[n // 2]

            # Calculate Q1
            q1_pos = n // 4
            if n % 4 == 0:
                q1 = (sorted_counts[q1_pos - 1] + sorted_counts[q1_pos]) / 2
            else:
                q1 = sorted_counts[q1_pos]

            # Calculate Q3
            q3_pos = (3 * n) // 4
            if n % 4 == 0:
                q3 = (sorted_counts[q3_pos - 1] + sorted_counts[q3_pos]) / 2
            else:
                q3 = sorted_counts[q3_pos]

            medians.append(median)
            q1s.append(q1)
            q3s.append(q3)
            maxes.append(max(sorted_counts))

    # Find the maximum value for normalization (using Q3 as the max reference)
    max_value = max(q3s) if q3s else 1

    # Create seasonal counts with normalized values
    seasonal_counts = []
    for month, (median, q1, q3, max_count) in enumerate(zip(medians, q1s, q3s, maxes), 1):
        seasonal_counts.append(
            SeasonalCount(
                species=species,
                month=month,
                absolute_avg=round(median),
                relative_avg=round(median / max_value, 2) if max_value > 0 else 0,
                q1_avg=round(q1),
                q3_avg=round(q3),
                max_count=round(max_count),
                recent_count=round(recent_counts.get(month, 0)),
            )
        )

    return seasonal_counts


if __name__ == "__main__":
    get_seasonal_analysis()
