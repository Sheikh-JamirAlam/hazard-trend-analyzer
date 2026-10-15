from dataclasses import dataclass
from datetime import date
import math

from app.services.normalization import Observation

BASELINE_START_YEAR = 1981
BASELINE_END_YEAR = 2010
BASELINE_PERCENTILE = 95
MIN_BASELINE_COVERAGE = 0.8


class InsufficientBaselineData(ValueError):
    pass


@dataclass(frozen=True)
class HeatwaveEvent:
    start_date: date
    end_date: date
    duration_days: int
    mean_excess_celsius: float


def calculate_threshold(
    observations: list[Observation], percentile: float = BASELINE_PERCENTILE
) -> float:
    values = sorted(
        item.maximum_celsius
        for item in observations
        if item.maximum_celsius is not None
    )
    expected = len(observations)
    if not values or expected == 0 or len(values) / expected < MIN_BASELINE_COVERAGE:
        raise InsufficientBaselineData(
            "The 1981–2010 baseline has less than 80% valid daily observations."
        )
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")

    # Linear interpolation using position (n - 1) * percentile / 100.
    position = (len(values) - 1) * percentile / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    return float(values[lower] + (values[upper] - values[lower]) * (position - lower))


def detect_heatwaves(
    observations: list[Observation], threshold_celsius: float, minimum_days: int = 3
) -> list[HeatwaveEvent]:
    if not math.isfinite(threshold_celsius):
        raise ValueError("threshold_celsius must be finite")
    if minimum_days < 1:
        raise ValueError("minimum_days must be at least 1")

    events: list[HeatwaveEvent] = []
    run: list[Observation] = []

    def flush() -> None:
        if len(run) >= minimum_days:
            values = [item.maximum_celsius for item in run]
            excess = [
                value - threshold_celsius for value in values if value is not None]
            events.append(
                HeatwaveEvent(
                    start_date=run[0].day,
                    end_date=run[-1].day,
                    duration_days=len(run),
                    mean_excess_celsius=sum(excess) / len(excess),
                )
            )
        run.clear()

    previous_day: date | None = None
    for item in observations:
        is_consecutive = previous_day is None or (
            item.day - previous_day).days == 1
        is_hot = item.maximum_celsius is not None and item.maximum_celsius > threshold_celsius
        if not is_consecutive or not is_hot:
            flush()
        if is_hot:
            run.append(item)
        previous_day = item.day
    flush()
    return events
