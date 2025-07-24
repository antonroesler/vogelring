from api.models.dashboard import Dashboard, SimpleBirdMeta, SimplePlaceMeta, RollingYearCountPerMonth
from api.models.sightings import Sighting
from api.db import loader
from datetime import date, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


def get_dashboard(user: str) -> Dashboard:
    logger.info("Generating dashboard data")
    sightings: list[Sighting] = loader.get_sightings(user=user)
    today = date.today()

    # Sort sightings by date for efficient processing
    dated_sightings = [s for s in sightings if s.date is not None]
    dated_sightings.sort(key=lambda x: x.date, reverse=True)
    logger.debug(f"Found {len(dated_sightings)} dated sightings out of {len(sightings)} total sightings")

    # Calculate basic counts
    total_sightings = len(sightings)
    total_birds = len({(s.ring, s.species) for s in sightings if s.ring is not None and s.species is not None})
    logger.debug(f"Total sightings: {total_sightings}, Total unique birds: {total_birds}")

    # Today's and yesterday's counts
    bird_count_today = sum(1 for s in dated_sightings if s.date == today)
    bird_count_yesterday = sum(1 for s in dated_sightings if s.date == today - timedelta(days=1))
    logger.debug(f"Birds today: {bird_count_today}, Birds yesterday: {bird_count_yesterday}")

    # This week and last week counts
    today_weekday = today.weekday()
    week_start = today - timedelta(days=today_weekday)
    last_week_start = week_start - timedelta(days=7)

    bird_count_this_week = sum(1 for s in dated_sightings if week_start <= s.date <= today)
    bird_count_last_week = sum(1 for s in dated_sightings if last_week_start <= s.date < week_start)
    logger.debug(f"Birds this week: {bird_count_this_week}, Birds last week: {bird_count_last_week}")

    # Calculate strike days
    strike_day_count = 0
    current_date = today
    dates_with_sightings = {s.date for s in dated_sightings}

    while current_date in dates_with_sightings:
        strike_day_count += 1
        current_date -= timedelta(days=1)
    logger.debug(f"Strike day count: {strike_day_count}")

    # Calculate rolling year counts per month per species
    rolling_year_counts: dict[str, list[RollingYearCountPerMonth]] = defaultdict(list)
    if today.month == 12:
        twelve_months_ago = date(year=today.year, month=1, day=1)
    else:
        twelve_months_ago = date(year=today.year - 1, month=today.month + 1, day=1)

    for s in dated_sightings:
        if s.date >= twelve_months_ago and s.species is not None:  # Only process if species exists
            year = s.date.year
            month = s.date.month
            rolling_year_counts[s.species].append(RollingYearCountPerMonth(year=year, month=month, count=1))

    # Aggregate counts per month
    for species, counts in rolling_year_counts.items():
        aggregated_counts = defaultdict(int)
        for count in counts:
            key = (count.year, count.month)
            aggregated_counts[key] += 1

        rolling_year_counts[species] = [
            RollingYearCountPerMonth(year=year, month=month, count=count)
            for (year, month), count in aggregated_counts.items()
        ]
    logger.debug(f"Generated rolling year counts for {len(rolling_year_counts)} species")

    # Calculate top 3 birds this year
    this_year_sightings = [s for s in dated_sightings if s.date.year == today.year]
    bird_counts = defaultdict(int)
    for s in this_year_sightings:
        if s.ring is not None and s.species is not None:  # Only count if both ring and species exist
            bird_counts[(s.species, s.ring)] += 1

    top_3_birds = sorted(
        [(species, ring, count) for (species, ring), count in bird_counts.items()], key=lambda x: x[2], reverse=True
    )[:3]

    top_3_birds_meta = [
        SimpleBirdMeta(species=species, ring=ring, sighting_count=count) for species, ring, count in top_3_birds
    ]
    logger.debug(f"Top 3 birds this year: {[f'{b.species} ({b.ring}): {b.sighting_count}' for b in top_3_birds_meta]}")

    # Calculate top 3 places this year
    place_counts = defaultdict(int)
    for s in this_year_sightings:
        if s.place is not None:  # Only count if place exists
            place_counts[s.place] += 1

    top_3_places = sorted([(place, count) for place, count in place_counts.items()], key=lambda x: x[1], reverse=True)[
        :3
    ]

    top_3_places_meta = [SimplePlaceMeta(place=place, count=count) for place, count in top_3_places]
    logger.debug(f"Top 3 places this year: {[f'{p.place}: {p.count}' for p in top_3_places_meta]}")

    logger.info("Dashboard data generation complete")
    return Dashboard(
        total_sightings=total_sightings,
        total_birds=total_birds,
        bird_count_today=bird_count_today,
        bird_count_yesterday=bird_count_yesterday,
        bird_count_this_week=bird_count_this_week,
        bird_count_last_week=bird_count_last_week,
        strike_day_count=strike_day_count,
        rolling_year_count_per_month_per_species=dict(rolling_year_counts),
        top_3_birds_this_year=top_3_birds_meta,
        top_3_places_this_year=top_3_places_meta,
    )
