from dataclasses import dataclass
from datetime import date, timedelta
import math

from app.services.weather_provider import DailyTemperature

MIN_PLAUSIBLE_CELSIUS = -90.0
MAX_PLAUSIBLE_CELSIUS = 70.0


@dataclass(frozen=True)
class Observation:
    day: date
    maximum_celsius: float | None


@dataclass(frozen=True)
class DataQualitySummary:
    expected_days: int
    observed_days: int
    missing_days: int
    excluded_invalid_observations: int


@dataclass(frozen=True)
class NormalizedWeather:
    observations: list[Observation]
    quality: DataQualitySummary


def normalize_observations(
    source: list[DailyTemperature], start_date: date, end_date: date
) -> NormalizedWeather:
    if start_date > end_date:
        raise ValueError("start_date must be on or before end_date")

    by_date: dict[date, float | None] = {}
    excluded = 0
    for item in source:
        if item.day < start_date or item.day > end_date:
            excluded += 1
            continue
        if item.day in by_date:
            excluded += 1
            continue
        value = item.maximum_celsius
        if value is not None:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value < MIN_PLAUSIBLE_CELSIUS
                or value > MAX_PLAUSIBLE_CELSIUS
            ):
                excluded += 1
                continue
        by_date[item.day] = None if value is None else float(value)

    expected_days = (end_date - start_date).days + 1
    observations = [
        Observation(day, by_date.get(day))
        for day in (start_date + timedelta(days=index) for index in range(expected_days))
    ]
    observed_days = sum(
        item.maximum_celsius is not None for item in observations)
    return NormalizedWeather(
        observations=observations,
        quality=DataQualitySummary(
            expected_days=expected_days,
            observed_days=observed_days,
            missing_days=expected_days - observed_days,
            excluded_invalid_observations=excluded,
        ),
    )
