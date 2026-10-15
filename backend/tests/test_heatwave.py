from datetime import date, timedelta

import pytest

from app.services.heatwave import (
    InsufficientBaselineData,
    calculate_threshold,
    detect_heatwaves,
)
from app.services.normalization import Observation


def observations(values: list[float | None], start: date = date(2020, 1, 1)) -> list[Observation]:
    return [Observation(start + timedelta(days=index), value) for index, value in enumerate(values)]


def test_three_hot_days_form_one_event_and_intensity_is_mean_excess() -> None:
    events = detect_heatwaves(observations([31, 32, 33, 34, 29]), 30)
    assert len(events) == 1
    assert events[0].duration_days == 4
    assert events[0].mean_excess_celsius == pytest.approx(2.5)


def test_two_hot_days_do_not_form_an_event() -> None:
    assert detect_heatwaves(observations([31, 32]), 30) == []


def test_equal_threshold_null_and_missing_date_break_a_run() -> None:
    series = observations([31, 32, 30, 31, None, 31, 32, 33])
    series.append(Observation(date(2020, 1, 10), 34))
    events = detect_heatwaves(series, 30)
    assert [(event.start_date, event.duration_days) for event in events] == [
        (date(2020, 1, 6), 3)
    ]


def test_cross_year_event_is_preserved() -> None:
    events = detect_heatwaves(
        observations([31, 31, 31], date(2020, 12, 30)), 30
    )
    assert events[0].start_date == date(2020, 12, 30)
    assert events[0].end_date == date(2021, 1, 1)


def test_percentile_interpolates_and_rejects_insufficient_baseline_coverage() -> None:
    assert calculate_threshold(observations(
        [0, 10, 20, 30]), 50) == pytest.approx(15)
    with pytest.raises(InsufficientBaselineData):
        calculate_threshold(observations([None, 12, None, None]))


def test_detector_rejects_invalid_threshold_or_event_length() -> None:
    with pytest.raises(ValueError):
        detect_heatwaves(observations([31]), float("nan"))
    with pytest.raises(ValueError):
        detect_heatwaves(observations([31]), 30, minimum_days=0)
