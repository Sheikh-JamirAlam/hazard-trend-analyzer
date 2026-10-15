from datetime import date, timedelta

from app.services.analysis import build_response
from app.services.weather_provider import DailyTemperature, WeatherResult


def _weather(start: date, values: list[float | None], end: date) -> WeatherResult:
    return WeatherResult(
        latitude=28.6,
        longitude=77.2,
        start_date=start,
        end_date=end,
        temperature_unit="°C",
        observations=[
            DailyTemperature(start + timedelta(days=index), value)
            for index, value in enumerate(values)
        ],
    )


def test_response_summary_and_annual_values_use_detected_events() -> None:
    baseline_start = date(1981, 1, 1)
    baseline_end = date(2010, 12, 31)
    baseline_days = (baseline_end - baseline_start).days + 1
    baseline = _weather(baseline_start, [20.0] * baseline_days, baseline_end)

    analysis_start = date(2020, 1, 1)
    analysis_end = date(2020, 12, 31)
    selected = _weather(
        analysis_start, [21.0, 22.0, 23.0, 20.0, 21.0], analysis_end)

    response = build_response(
        latitude=28.6,
        longitude=77.2,
        location_label="Delhi",
        start_year=2020,
        end_year=2020,
        weather=selected,
        baseline_weather=baseline,
    )

    assert response.threshold_celsius == 20.0
    assert response.total_events == 1
    assert response.summary.mean_event_duration_days == 3.0
    assert response.summary.mean_event_intensity_celsius == 2.0
    assert response.annual_metrics[0].event_count == 1
    assert response.annual_metrics[0].data_available
    assert response.data_quality.expected_days == 366
    assert response.data_quality.missing_days == 361


def test_cross_year_event_uses_start_year_and_unavailable_year_is_distinct() -> None:
    baseline_start = date(1981, 1, 1)
    baseline_end = date(2010, 12, 31)
    baseline_days = (baseline_end - baseline_start).days + 1
    baseline = _weather(baseline_start, [20.0] * baseline_days, baseline_end)
    start = date(2020, 12, 30)
    selected = _weather(
        start,
        [31.0, 32.0, 33.0, 34.0, 20.0],
        date(2021, 1, 3),
    )

    response = build_response(
        latitude=28.6,
        longitude=77.2,
        location_label=None,
        start_year=2020,
        end_year=2022,
        weather=selected,
        baseline_weather=baseline,
    )

    assert [row.event_count for row in response.annual_metrics] == [1, 0, 0]
    assert [row.data_available for row in response.annual_metrics] == [
        True, True, False]
